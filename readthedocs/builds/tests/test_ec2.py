from unittest import mock

from botocore.exceptions import ClientError
from django.core.cache import cache
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds import ec2
from readthedocs.builds.constants import BUILD_STATE_BUILDING
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.builds.tasks import set_build_isolated_desired_capacity
from readthedocs.projects.models import Project


ASG_NAME = "build-isolated"


def group(desired, max_size=100):
    return {"AutoScalingGroups": [{"DesiredCapacity": desired, "MaxSize": max_size}]}


@override_settings(
    DEBUG=False,
    RTD_DOCKER_COMPOSE=False,
    RTD_AWS_SCALE_IN_REGION_NAME="us-east-2",
    RTD_BUILD_ISOLATED_ASG_NAME=ASG_NAME,
    RTD_BUILD_ISOLATED_BUFFER=5,
)
@mock.patch("readthedocs.builds.ec2.boto3.client")
class EnsureWarmBufferTests(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)

    def build(self, state=BUILD_STATE_TRIGGERED, dispatched=True):
        return get(
            Build,
            project=self.project,
            version=self.version,
            state=state,
            dispatched_date=timezone.now() if dispatched else None,
        )

    def asg(self, boto3_client, desired, max_size=100):
        asg = boto3_client.return_value
        asg.describe_auto_scaling_groups.return_value = group(desired, max_size)
        return asg

    def test_lifts_desired_to_dispatched_plus_buffer(self, boto3_client):
        asg = self.asg(boto3_client, desired=6)
        self.build(BUILD_STATE_TRIGGERED)
        self.build(BUILD_STATE_BUILDING)
        # Finished: its instance is gone. Not dispatched: not on the fleet yet.
        self.build(BUILD_STATE_FINISHED)
        self.build(dispatched=False)

        ec2.ensure_warm_buffer()

        asg.describe_auto_scaling_groups.assert_called_once_with(AutoScalingGroupNames=[ASG_NAME])
        asg.set_desired_capacity.assert_called_once_with(
            AutoScalingGroupName=ASG_NAME,
            DesiredCapacity=2 + 5,
            HonorCooldown=False,
        )

    def test_never_lowers_desired(self, boto3_client):
        """Surplus idle instances are consumed by later dispatches, not terminated."""
        asg = self.asg(boto3_client, desired=30)
        self.build()

        ec2.ensure_warm_buffer()

        asg.set_desired_capacity.assert_not_called()

    def test_caps_at_max_size(self, boto3_client):
        asg = self.asg(boto3_client, desired=3, max_size=4)
        self.build()

        ec2.ensure_warm_buffer()

        asg.set_desired_capacity.assert_called_once_with(
            AutoScalingGroupName=ASG_NAME,
            DesiredCapacity=4,
            HonorCooldown=False,
        )

    @override_settings(RTD_BUILD_ISOLATED_ASG_NAME=None)
    def test_skips_without_an_asg_name(self, boto3_client):
        ec2.ensure_warm_buffer()

        boto3_client.assert_not_called()

    @override_settings(RTD_DOCKER_COMPOSE=True)
    def test_skips_in_development(self, boto3_client):
        ec2.ensure_warm_buffer()

        boto3_client.assert_not_called()

    def test_skips_when_the_group_is_missing(self, boto3_client):
        asg = boto3_client.return_value
        asg.describe_auto_scaling_groups.return_value = {"AutoScalingGroups": []}

        ec2.ensure_warm_buffer()

        asg.set_desired_capacity.assert_not_called()

    def test_never_raises(self, boto3_client):
        """A failed lift must not fail the dispatch; the next one retries."""
        asg = self.asg(boto3_client, desired=0)
        asg.set_desired_capacity.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "SetDesiredCapacity"
        )

        assert ec2.ensure_warm_buffer() is None

    @mock.patch("readthedocs.builds.tasks.ensure_warm_buffer")
    def test_periodic_task_lifts_the_warm_buffer(self, ensure_warm_buffer, boto3_client):
        assert set_build_isolated_desired_capacity() is True

        ensure_warm_buffer.assert_called_once_with()

    @mock.patch("readthedocs.builds.tasks.ensure_warm_buffer")
    def test_periodic_task_skips_while_another_run_holds_the_lock(
        self, ensure_warm_buffer, boto3_client
    ):
        lock_id = f"{set_build_isolated_desired_capacity.name}-lock"
        cache.add(lock_id, "other-run", 10)
        self.addCleanup(cache.delete, lock_id)

        assert set_build_isolated_desired_capacity() is False

        ensure_warm_buffer.assert_not_called()
