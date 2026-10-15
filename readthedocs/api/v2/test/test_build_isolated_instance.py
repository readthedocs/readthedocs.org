from unittest import mock

from botocore.exceptions import ClientError
from django.test import TestCase
from django.test import override_settings
from django_dynamic_fixture import get
from rest_framework.test import APIClient

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project


INSTANCE_ID = "i-0123456789abcdef0"
BUILDER = f"build-isolated-{INSTANCE_ID}"


def client_error(message):
    return ClientError(
        {"Error": {"Code": "ValidationError", "Message": message}},
        "TerminateInstanceInAutoScalingGroup",
    )


@override_settings(
    DEBUG=False,
    RTD_DOCKER_COMPOSE=False,
    RTD_AWS_SCALE_IN_REGION_NAME="us-east-2",
)
@mock.patch("readthedocs.builds.ec2.boto3.client")
class BuildIsolatedInstanceTests(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)
        self.build = get(
            Build,
            project=self.project,
            version=self.version,
            builder=BUILDER,
            state=BUILD_STATE_FINISHED,
            dispatched_date=None,
        )
        _, self.key = BuildAPIKey.objects.create_key(project=self.project)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.key}")
        self.protect_url = f"/api/v2/build/{self.build.pk}/instance/protect/"
        self.release_url = f"/api/v2/build/{self.build.pk}/instance/release/"

    def asg(self, boto3_client):
        return boto3_client.return_value

    def test_protect_requires_a_build_api_key(self, boto3_client):
        resp = APIClient().post(self.protect_url, {"builder": BUILDER})

        assert resp.status_code == 403
        boto3_client.assert_not_called()

    def test_protect_rejects_builds_of_other_projects(self, boto3_client):
        other = get(Build, project=get(Project), dispatched_date=None)

        resp = self.client.post(f"/api/v2/build/{other.pk}/instance/protect/", {"builder": BUILDER})

        assert resp.status_code == 404
        boto3_client.assert_not_called()

    def test_protect_rejects_hostnames_outside_the_isolated_fleet(self, boto3_client):
        resp = self.client.post(self.protect_url, {"builder": "build-default-i-0123456789abcdef0"})

        assert resp.status_code == 400
        boto3_client.assert_not_called()

    def test_protect_claims_the_build_and_protects_the_instance(self, boto3_client):
        self.build.builder = ""
        self.build.save()

        resp = self.client.post(self.protect_url, {"builder": BUILDER})

        assert resp.status_code == 204
        self.build.refresh_from_db()
        assert self.build.builder == BUILDER
        boto3_client.return_value.set_instance_protection.assert_called_once_with(
            InstanceIds=[INSTANCE_ID],
            AutoScalingGroupName="build-isolated",
            ProtectedFromScaleIn=True,
        )

    def test_release_rejects_unclaimed_builds(self, boto3_client):
        self.build.builder = ""
        self.build.save()

        resp = self.client.post(self.release_url)

        assert resp.status_code == 400
        boto3_client.assert_not_called()

    def test_release_terminates_the_instance_and_shrinks_the_fleet(self, boto3_client):
        """A finished build takes its instance and its demand away together."""
        asg = self.asg(boto3_client)

        resp = self.client.post(self.release_url)

        assert resp.status_code == 200
        assert resp.json() == {"state": "terminated", "decremented": True}
        asg.set_instance_protection.assert_called_once_with(
            InstanceIds=[INSTANCE_ID],
            AutoScalingGroupName="build-isolated",
            ProtectedFromScaleIn=False,
        )
        asg.terminate_instance_in_auto_scaling_group.assert_called_once_with(
            InstanceId=INSTANCE_ID,
            ShouldDecrementDesiredCapacity=True,
        )
        asg.describe_auto_scaling_groups.assert_not_called()
        assert not BuildAPIKey.objects.is_valid(self.key)

    def test_release_retries_without_decrement_at_min_size(self, boto3_client):
        asg = self.asg(boto3_client)
        asg.terminate_instance_in_auto_scaling_group.side_effect = [
            client_error("Currently, desiredSize equals minSize (5)."),
            None,
        ]

        resp = self.client.post(self.release_url)

        assert resp.json() == {"state": "terminated", "decremented": False}
        assert asg.terminate_instance_in_auto_scaling_group.call_args_list == [
            mock.call(InstanceId=INSTANCE_ID, ShouldDecrementDesiredCapacity=True),
            mock.call(InstanceId=INSTANCE_ID, ShouldDecrementDesiredCapacity=False),
        ]

    def test_release_treats_a_missing_instance_as_terminated(self, boto3_client):
        asg = self.asg(boto3_client)
        asg.terminate_instance_in_auto_scaling_group.side_effect = client_error(
            f"Instance Id not found - No managed instance found for instance ID: {INSTANCE_ID}"
        )

        resp = self.client.post(self.release_url)

        assert resp.json() == {"state": "terminated", "decremented": False}
        assert not BuildAPIKey.objects.is_valid(self.key)

    def test_release_reports_failure_and_keeps_the_key_for_a_retry(self, boto3_client):
        asg = self.asg(boto3_client)
        asg.terminate_instance_in_auto_scaling_group.side_effect = client_error("boom")

        resp = self.client.post(self.release_url)

        assert resp.status_code == 200
        assert resp.json() == {"state": "failed", "decremented": False}
        assert BuildAPIKey.objects.is_valid(self.key)

    def test_release_keeps_the_instance_when_the_project_asks(self, boto3_client):
        asg = self.asg(boto3_client)
        get(
            Feature,
            projects=[self.project],
            feature_id=Feature.KEEP_BUILD_ISOLATED_INSTANCE,
            default_true=False,
            future_default_true=False,
        )

        resp = self.client.post(self.release_url)

        assert resp.json() == {"state": "kept", "decremented": False}
        asg.set_instance_protection.assert_called_once_with(
            InstanceIds=[INSTANCE_ID],
            AutoScalingGroupName="build-isolated",
            ProtectedFromScaleIn=False,
        )
        asg.terminate_instance_in_auto_scaling_group.assert_not_called()
        assert not BuildAPIKey.objects.is_valid(self.key)

    @override_settings(RTD_DOCKER_COMPOSE=True)
    def test_release_skips_aws_in_development(self, boto3_client):
        resp = self.client.post(self.release_url)

        assert resp.json() == {"state": "kept", "decremented": False}
        boto3_client.assert_not_called()
