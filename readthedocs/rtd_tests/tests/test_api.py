import datetime
import json
from unittest import mock

import dateutil
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get
from rest_framework import status
from rest_framework.test import APIClient

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.api.v2.views.integrations import (
    BITBUCKET_EVENT_HEADER,
    BITBUCKET_SIGNATURE_HEADER,
    GITHUB_CREATE,
    GITHUB_DELETE,
    GITHUB_EVENT_HEADER,
    GITHUB_PING,
    GITHUB_PULL_REQUEST,
    GITHUB_PULL_REQUEST_CLOSED,
    GITHUB_PULL_REQUEST_OPENED,
    GITHUB_PULL_REQUEST_REOPENED,
    GITHUB_PULL_REQUEST_SYNC,
    GITHUB_PUSH,
    GITHUB_SIGNATURE_HEADER,
    GITLAB_MERGE_REQUEST,
    GITLAB_MERGE_REQUEST_CLOSE,
    GITLAB_MERGE_REQUEST_MERGE,
    GITLAB_MERGE_REQUEST_REOPEN,
    GITLAB_MERGE_REQUEST_UPDATE,
    GITLAB_NULL_HASH,
    GITLAB_PUSH,
    GITLAB_TAG_PUSH,
    GITLAB_TOKEN_HEADER,
    GitHubWebhookView,
    GitLabWebhookView,
    WebhookMixin,
)
from readthedocs.builds.constants import (
    BRANCH,
    BUILD_STATE_CLONING,
    BUILD_STATE_FINISHED,
    BUILD_STATE_TRIGGERED,
    BUILD_STATE_UPLOADING,
    EXTERNAL,
    EXTERNAL_VERSION_STATE_CLOSED,
    LATEST,
    TAG,
)
from readthedocs.builds.models import APIVersion, Build, BuildCommandResult, Version
from readthedocs.doc_builder.exceptions import BuildCancelled, BuildMaxConcurrencyError
from readthedocs.integrations.models import GenericAPIWebhook, Integration
from readthedocs.notifications.constants import READ, UNREAD
from readthedocs.notifications.models import Notification
from readthedocs.oauth.models import (
    GitHubAccountType,
    GitHubAppInstallation,
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)
from readthedocs.oauth.services import GitHubAppService
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import (
    APIProject,
    Domain,
    EnvironmentVariable,
    Feature,
    Project,
)
from readthedocs.aws.security_token_service import AWSS3TemporaryCredentials
from readthedocs.projects.notifications import MESSAGE_PROJECT_DEPRECATED_WEBHOOK
from readthedocs.subscriptions.constants import TYPE_CONCURRENT_BUILDS
from readthedocs.subscriptions.products import RTDProductFeature
from readthedocs.vcs_support.backends.git import parse_version_from_ref


def get_signature(integration, payload):
    if not isinstance(payload, str):
        payload = json.dumps(payload, separators=(",", ":"))
    return "sha256=" + WebhookMixin.get_digest(
        secret=integration.secret,
        # When the test client sends the payload, it doesn't
        # separate the json keys with spaces, so when getting
        # the digest, we need to remove the spaces.
        msg=payload,
    )


@override_settings(PUBLIC_DOMAIN="readthedocs.io")
class APIBuildTests(TestCase):
    fixtures = ["eric.json", "test_data.json"]

    def setUp(self):
        self.user = User.objects.get(username="eric")
        self.project = get(Project, users=[self.user])
        self.version = self.project.versions.get(slug=LATEST)

    def test_healthcheck(self):
        # Build cloning state
        build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_CLONING,
            builder="build-a1b2c3",
            success=False,
        )
        self.assertIsNone(build.healthcheck)

        client = APIClient()
        r = client.post(reverse("build-healthcheck", args=(build.pk,), query={"builder": "build-a1b2c3"}))
        build.refresh_from_db()

        self.assertEqual(r.status_code, 204)
        self.assertIsNotNone(build.healthcheck)

        # Build invalid builder
        build.healthcheck = None
        build.save()

        client = APIClient()
        r = client.post(reverse("build-healthcheck", args=(build.pk,), query={"builder": "build-invalid"}))
        build.refresh_from_db()

        self.assertEqual(r.status_code, 404)
        self.assertIsNone(build.healthcheck)

        # Build finished state
        build.state = BUILD_STATE_FINISHED
        build.healthcheck = None
        build.save()

        client = APIClient()
        r = client.post(reverse("build-healthcheck", args=(build.pk,), query={"builder": "build-a1b2c3"}))
        build.refresh_from_db()

        self.assertEqual(r.status_code, 404)
        self.assertIsNone(build.healthcheck)


    def test_reset_build(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_CLONING,
            success=False,
            output="Output",
            error="Error",
            exit_code=9,
            builder="Builder",
            cold_storage=True,
        )
        command = get(
            BuildCommandResult,
            build=build,
        )
        build.commands.add(command)

        Notification.objects.add(
            attached_to=build,
            message_id=BuildCancelled.SKIPPED_EXIT_CODE_183,
        )

        self.assertEqual(build.commands.count(), 1)
        self.assertEqual(build.notifications.count(), 1)

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(self.project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        r = client.post(reverse("build-reset", args=(build.pk,)))

        self.assertEqual(r.status_code, 204)
        build.refresh_from_db()
        self.assertEqual(build.project, self.project)
        self.assertEqual(build.version, self.version)
        self.assertEqual(build.state, BUILD_STATE_TRIGGERED)
        self.assertEqual(build.status, "")
        self.assertTrue(build.success)
        self.assertEqual(build.output, "")
        self.assertEqual(build.error, "")
        self.assertIsNone(build.exit_code)
        self.assertEqual(build.builder, "")
        self.assertFalse(build.cold_storage)
        self.assertEqual(build.commands.count(), 0)
        self.assertEqual(build.notifications.count(), 0)

    @mock.patch("readthedocs.api.v2.views.model_views.get_s3_build_tools_scoped_credentials")
    @mock.patch("readthedocs.api.v2.views.model_views.get_s3_build_media_scoped_credentials")
    def test_get_temporary_credentials_for_build(self, get_s3_build_media_scoped_credentials, get_s3_build_tools_scoped_credentials):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_UPLOADING,
            success=False,
            output="Output",
            error="Error",
            exit_code=0,
            builder="Builder",
            cold_storage=True,
        )

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(self.project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")
        get_s3_build_media_scoped_credentials.return_value = AWSS3TemporaryCredentials(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
            region_name="us-east-1",
            bucket_name="readthedocs-media",
        )
        r = client.post(reverse("build-credentials-for-storage", args=(build.pk,)), {"type": "build_media"})
        assert r.status_code == 200
        assert r.data == {
            "s3": {
                "access_key_id": "access_key_id",
                "secret_access_key": "secret_access_key",
                "session_token": "session_token",
                "region_name": "us-east-1",
                "bucket_name": "readthedocs-media",
            }
        }

        get_s3_build_media_scoped_credentials.assert_called_once_with(
            build=build,
            duration=60 * 30,
        )

        get_s3_build_tools_scoped_credentials.return_value = AWSS3TemporaryCredentials(
            access_key_id="access_key_id",
            secret_access_key="secret_access_key",
            session_token="session_token",
            region_name="us-east-1",
            bucket_name="readthedocs-build-tools",
        )
        r = client.post(reverse("build-credentials-for-storage", args=(build.pk,)), {"type": "build_tools"})
        assert r.status_code == 200
        assert r.data == {
            "s3": {
                "access_key_id": "access_key_id",
                "secret_access_key": "secret_access_key",
                "session_token": "session_token",
                "region_name": "us-east-1",
                "bucket_name": "readthedocs-build-tools",
            }
        }

        get_s3_build_tools_scoped_credentials.assert_called_once_with(
            build=build,
            duration=60 * 30,
        )

    def test_api_does_not_have_private_config_key_superuser(self):
        client = APIClient()
        client.login(username="super", password="test")
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = Build.objects.create(project=project, version=version)

        resp = client.get("/api/v2/build/{}/".format(build.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("config", resp.data)
        self.assertNotIn("_config", resp.data)

    def test_api_does_not_have_private_config_key_normal_user(self):
        client = APIClient()
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = Build.objects.create(project=project, version=version)

        resp = client.get("/api/v2/build/{}/".format(build.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("config", resp.data)
        self.assertNotIn("_config", resp.data)

    def test_save_same_config_using_patch(self):
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build_one = Build.objects.create(project=project, version=version)

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        resp = client.patch(
            "/api/v2/build/{}/".format(build_one.pk),
            {"config": {"one": "two"}},
            format="json",
        )
        self.assertEqual(resp.data["config"], {"one": "two"})

        build_two = Build.objects.create(project=project, version=version)
        resp = client.patch(
            "/api/v2/build/{}/".format(build_two.pk),
            {"config": {"one": "two"}},
            format="json",
        )
        self.assertEqual(resp.data["config"], {"one": "two"})

        resp = client.get("/api/v2/build/{}/".format(build_one.pk))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        build = resp.data
        self.assertEqual(build["config"], {"one": "two"})

        # Checking the values from the db, just to be sure the
        # api isn't lying.
        self.assertEqual(
            Build.objects.get(pk=build_one.pk)._config,
            {"one": "two"},
        )
        self.assertEqual(
            Build.objects.get(pk=build_two.pk)._config,
            {Build.CONFIG_KEY: build_one.pk},
        )

    def test_response_building(self):
        """The ``view docs`` attr should return a link to the dashboard."""
        client = APIClient()
        client.login(username="super", password="test")
        project = get(
            Project,
            language="en",
            main_language_project=None,
        )
        version = get(
            Version,
            project=project,
            built=False,
            uploaded=False,
        )
        build = get(
            Build,
            project=project,
            version=version,
            state="cloning",
            exit_code=0,
        )
        resp = client.get("/api/v2/build/{build}/".format(build=build.pk))
        self.assertEqual(resp.status_code, 200)

        dashboard_url = reverse(
            "project_version_detail",
            kwargs={
                "project_slug": project.slug,
                "version_slug": version.slug,
            },
        )

        build = resp.data
        self.assertEqual(build["state"], "cloning")
        self.assertEqual(build["error"], "")
        self.assertEqual(build["exit_code"], 0)
        self.assertEqual(build["success"], True)
        self.assertTrue(build["docs_url"].endswith(dashboard_url))
        self.assertTrue(build["docs_url"].startswith("https://"))

    @override_settings(DOCROOT="/home/docs/checkouts/readthedocs.org/user_builds")
    def test_response_finished_and_success(self):
        """The ``view docs`` attr should return a link to the docs."""
        client = APIClient()
        client.login(username="super", password="test")
        project = get(
            Project,
            language="en",
            slug="myproject",
            main_language_project=None,
        )
        version = get(
            Version,
            slug="myversion",
            project=project,
            built=True,
            uploaded=True,
        )
        build = get(
            Build,
            project=project,
            version=version,
            state="finished",
            exit_code=0,
        )
        buildcommandresult = get(
            BuildCommandResult,
            build=build,
            command="python -m pip install --upgrade --no-cache-dir pip setuptools<58.3.0",
            exit_code=0,
        )
        resp = client.get("/api/v2/build/{build}/".format(build=build.pk))
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        docs_url = f"http://{project.slug}.readthedocs.io/en/{version.slug}/"
        self.assertEqual(build["state"], "finished")
        self.assertEqual(build["error"], "")
        self.assertEqual(build["exit_code"], 0)
        self.assertEqual(build["success"], True)
        self.assertEqual(build["docs_url"], docs_url)
        # Verify the path is trimmed
        self.assertEqual(
            build["commands"][0]["command"],
            "python -m pip install --upgrade --no-cache-dir pip setuptools<58.3.0",
        )

    def test_response_finished_and_fail(self):
        """The ``view docs`` attr should return a link to the dashboard."""
        client = APIClient()
        client.login(username="super", password="test")
        project = get(
            Project,
            language="en",
            main_language_project=None,
        )
        version = get(
            Version,
            project=project,
            built=False,
            uploaded=False,
        )
        build = get(
            Build,
            project=project,
            version=version,
            state="finished",
            success=False,
            exit_code=1,
        )

        resp = client.get("/api/v2/build/{build}/".format(build=build.pk))
        self.assertEqual(resp.status_code, 200)

        dashboard_url = reverse(
            "project_version_detail",
            kwargs={
                "project_slug": project.slug,
                "version_slug": version.slug,
            },
        )
        build = resp.data
        self.assertEqual(build["state"], "finished")
        self.assertEqual(build["error"], "")
        self.assertEqual(build["exit_code"], 1)
        self.assertEqual(build["success"], False)
        self.assertTrue(build["docs_url"].endswith(dashboard_url))
        self.assertTrue(build["docs_url"].startswith("https://"))

    def test_make_build_without_permission(self):
        """Ensure anonymous/non-staff users cannot write the build endpoint."""
        client = APIClient()

        def _try_post():
            resp = client.post(
                "/api/v2/build/",
                {
                    "project": 1,
                    "version": 1,
                    "success": True,
                    "output": "Test Output",
                    "error": "Test Error",
                },
                format="json",
            )
            self.assertEqual(resp.status_code, 403)

        _try_post()

        api_user = get(User, is_staff=False, password="test")
        assert api_user.is_staff is False
        client.force_authenticate(user=api_user)
        _try_post()

    def test_update_build_without_permission(self):
        """Ensure anonymous/non-staff users cannot update build endpoints."""
        client = APIClient()
        api_user = get(User, is_staff=False, password="test")
        client.force_authenticate(user=api_user)
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(Build, project=project, version=version, state="cloning")
        resp = client.put(
            "/api/v2/build/{}/".format(build.pk),
            {
                "project": 1,
                "version": 1,
                "state": "finished",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_make_build_protected_fields(self):
        """
        Ensure build api view delegates correct serializer.

        Build API keys should be able to read/write the `builder` property, but we
        don't expose this to end users via the API
        """
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(Build, project=project, version=version, builder="foo")
        client = APIClient()

        api_user = get(User, is_staff=False, password="test")
        client.force_authenticate(user=api_user)
        resp = client.get("/api/v2/build/{}/".format(build.pk), format="json")
        self.assertEqual(resp.status_code, 200)

        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")
        resp = client.get("/api/v2/build/{}/".format(build.pk), format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("builder", resp.data)

    def test_make_build_commands(self):
        """Create build commands."""
        _, build_api_key = BuildAPIKey.objects.create_key(self.project)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        build = get(Build, project=self.project, version=self.version, success=True)
        now = timezone.now()
        start_time = now - datetime.timedelta(seconds=5)
        end_time = now
        resp = client.post(
            "/api/v2/command/",
            {
                "build": build.pk,
                "command": "$CONDA_ENVS_PATH/$CONDA_DEFAULT_ENV/bin/python -m sphinx",
                "description": "Conda and Sphinx command",
                "exit_code": 0,
                "start_time": start_time,
                "end_time": end_time,
            },
            format="json",
        )
        resp = client.post(
            "/api/v2/command/",
            {
                "build": build.pk,
                "command": "$READTHEDOCS_VIRTUALENV_PATH/bin/python -m sphinx",
                "description": "Python and Sphinx command",
                "exit_code": 0,
                "start_time": start_time + datetime.timedelta(seconds=1),
                "end_time": end_time,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp = client.get(f"/api/v2/build/{build.pk}/")
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(len(build["commands"]), 2)
        self.assertEqual(build["commands"][0]["command"], "python -m sphinx")
        self.assertEqual(build["commands"][0]["run_time"], 5)
        self.assertEqual(
            build["commands"][0]["description"], "Conda and Sphinx command"
        )
        self.assertEqual(build["commands"][0]["exit_code"], 0)
        self.assertEqual(
            dateutil.parser.parse(build["commands"][0]["start_time"]), start_time
        )
        self.assertEqual(
            dateutil.parser.parse(build["commands"][0]["end_time"]), end_time
        )

        self.assertEqual(build["commands"][1]["command"], "python -m sphinx")
        self.assertEqual(
            build["commands"][1]["description"], "Python and Sphinx command"
        )

    def test_get_raw_log_success(self):
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(
            Build,
            project=project,
            version=version,
            builder="foo",
            state=BUILD_STATE_FINISHED,
        )
        get(
            BuildCommandResult,
            build=build,
            command="python setup.py install",
            output="Installing dependencies...",
        )
        get(
            BuildCommandResult,
            build=build,
            command="git checkout master",
            output='Switched to branch "master"',
        )
        client = APIClient()

        api_user = get(User)
        client.force_authenticate(user=api_user)
        resp = client.get("/api/v2/build/{}.txt".format(build.pk))
        self.assertEqual(resp.status_code, 200)

        self.assertIn("Read the Docs build information", resp.content.decode())
        self.assertIn("Build id: {}".format(build.id), resp.content.decode())
        self.assertIn("Project: {}".format(build.project.slug), resp.content.decode())
        self.assertIn("Version: {}".format(build.version.slug), resp.content.decode())
        self.assertIn("Commit: {}".format(build.commit), resp.content.decode())
        self.assertIn("Date: ", resp.content.decode())
        self.assertIn("State: finished", resp.content.decode())
        self.assertIn("Success: True", resp.content.decode())
        self.assertIn("[rtd-command-info]", resp.content.decode())
        self.assertIn(
            "python setup.py install\nInstalling dependencies...",
            resp.content.decode(),
        )
        self.assertIn(
            'git checkout master\nSwitched to branch "master"',
            resp.content.decode(),
        )

    def test_get_raw_log_building(self):
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(
            Build,
            project=project,
            version=version,
            builder="foo",
            success=False,
            exit_code=1,
            state="building",
        )
        get(
            BuildCommandResult,
            build=build,
            command="python setup.py install",
            output="Installing dependencies...",
            exit_code=1,
        )
        get(
            BuildCommandResult,
            build=build,
            command="git checkout master",
            output='Switched to branch "master"',
        )
        client = APIClient()

        api_user = get(User)
        client.force_authenticate(user=api_user)
        resp = client.get("/api/v2/build/{}.txt".format(build.pk))
        self.assertEqual(resp.status_code, 200)

        self.assertIn("Read the Docs build information", resp.content.decode())
        self.assertIn("Build id: {}".format(build.id), resp.content.decode())
        self.assertIn("Project: {}".format(build.project.slug), resp.content.decode())
        self.assertIn("Version: {}".format(build.version.slug), resp.content.decode())
        self.assertIn("Commit: {}".format(build.commit), resp.content.decode())
        self.assertIn("Date: ", resp.content.decode())
        self.assertIn("State: building", resp.content.decode())
        self.assertIn("Success: Unknow", resp.content.decode())
        self.assertIn("[rtd-command-info]", resp.content.decode())
        self.assertIn(
            "python setup.py install\nInstalling dependencies...",
            resp.content.decode(),
        )
        self.assertIn(
            'git checkout master\nSwitched to branch "master"',
            resp.content.decode(),
        )

    def test_get_raw_log_failure(self):
        project = Project.objects.get(pk=1)
        version = project.versions.first()
        build = get(
            Build,
            project=project,
            version=version,
            builder="foo",
            success=False,
            exit_code=1,
            state=BUILD_STATE_FINISHED,
        )
        get(
            BuildCommandResult,
            build=build,
            command="python setup.py install",
            output="Installing dependencies...",
            exit_code=1,
        )
        get(
            BuildCommandResult,
            build=build,
            command="git checkout master",
            output='Switched to branch "master"',
        )
        client = APIClient()

        api_user = get(User)
        client.force_authenticate(user=api_user)
        resp = client.get("/api/v2/build/{}.txt".format(build.pk))
        self.assertEqual(resp.status_code, 200)

        self.assertIn("Read the Docs build information", resp.content.decode())
        self.assertIn("Build id: {}".format(build.id), resp.content.decode())
        self.assertIn("Project: {}".format(build.project.slug), resp.content.decode())
        self.assertIn("Version: {}".format(build.version.slug), resp.content.decode())
        self.assertIn("Commit: {}".format(build.commit), resp.content.decode())
        self.assertIn("Date: ", resp.content.decode())
        self.assertIn("State: finished", resp.content.decode())
        self.assertIn("Success: False", resp.content.decode())
        self.assertIn("[rtd-command-info]", resp.content.decode())
        self.assertIn(
            "python setup.py install\nInstalling dependencies...",
            resp.content.decode(),
        )
        self.assertIn(
            'git checkout master\nSwitched to branch "master"',
            resp.content.decode(),
        )

    def test_get_invalid_raw_log(self):
        client = APIClient()

        api_user = get(User)
        client.force_authenticate(user=api_user)
        resp = client.get("/api/v2/build/{}.txt".format(404))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_build_filter_by_commit(self):
        """
        Create a build with commit
        Should return the list of builds according to the
        commit query params
        """
        project1 = Project.objects.get(pk=1)
        project2 = Project.objects.get(pk=2)
        version1 = project1.versions.first()
        version2 = project2.versions.first()
        get(Build, project=project1, version=version1, builder="foo", commit="test")
        get(Build, project=project2, version=version2, builder="foo", commit="other")
        client = APIClient()
        api_user = get(User, is_staff=False, password="test")
        client.force_authenticate(user=api_user)
        resp = client.get("/api/v2/build/", {"commit": "test"}, format="json")
        self.assertEqual(resp.status_code, 200)
        build = resp.data
        self.assertEqual(len(build["results"]), 1)

    def test_build_without_version(self):
        build = get(
            Build,
            project=self.project,
            version=None,
            state=BUILD_STATE_FINISHED,
            exit_code=0,
        )
        command = "python -m pip install --upgrade --no-cache-dir pip setuptools<58.3.0"
        get(
            BuildCommandResult,
            build=build,
            command=command,
            output="Running...",
            exit_code=0,
        )
        client = APIClient()
        client.force_authenticate(user=self.user)
        r = client.get(reverse("build-detail", args=(build.pk,)))
        assert r.status_code == 200
        assert r.data["version"] is None
        assert r.data["commands"][0]["command"] == command


class APITests(TestCase):
    fixtures = ["eric.json", "test_data.json"]

    def test_create_key_for_project_with_long_slug(self):
        user = get(User)
        project = get(Project, users=[user], slug="a" * 60)
        build_api_key_obj, build_api_key = BuildAPIKey.objects.create_key(project)
        self.assertTrue(BuildAPIKey.objects.is_valid(build_api_key))
        self.assertEqual(build_api_key_obj.name, "a" * 50)

    def test_revoke_build_api_key(self):
        user = get(User)
        project = get(Project, users=[user])
        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client = APIClient()
        revoke_url = "/api/v2/revoke/"
        self.assertTrue(BuildAPIKey.objects.is_valid(build_api_key))

        # Anonymous request.
        client.logout()
        resp = client.post(revoke_url)
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(BuildAPIKey.objects.is_valid(build_api_key))

        # Using user/password.
        client.force_login(user)
        resp = client.post(revoke_url)
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(BuildAPIKey.objects.is_valid(build_api_key))

        client.logout()
        resp = client.post(revoke_url, HTTP_AUTHORIZATION=f"Token {build_api_key}")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(BuildAPIKey.objects.is_valid(build_api_key))

    @override_settings(BUILD_TIME_LIMIT=600)
    def test_expiricy_key(self):
        project = get(Project)
        build_api_key_obj, build_api_key = BuildAPIKey.objects.create_key(project)
        expected = (build_api_key_obj.expiry_date - timezone.now()).seconds
        self.assertAlmostEqual(expected, 86400, delta=5)

        # Project with a custom containe time limit
        project.container_time_limit = 1200
        project.save()
        build_api_key_obj, build_api_key = BuildAPIKey.objects.create_key(project)
        expected = (build_api_key_obj.expiry_date - timezone.now()).seconds
        self.assertAlmostEqual(expected, 86400, delta=5)

    def test_user_doesnt_get_full_api_return(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)
        project = get(
            Project,
            main_language_project=None,
            readthedocs_yaml_path="bar",
        )
        client = APIClient()

        for user in [user_normal, user_admin]:
            client.force_authenticate(user=user)
            resp = client.get("/api/v2/project/%s/" % (project.pk))
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("readthedocs_yaml_path", resp.data)

        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        resp = client.get("/api/v2/project/%s/" % (project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("readthedocs_yaml_path", resp.data)
        self.assertEqual(resp.data["readthedocs_yaml_path"], "bar")

    def test_project_read_only_endpoints_for_normal_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        client.force_authenticate(user=user_normal)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/project/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow creating projects.
        resp = client.post("/api/v2/project/")
        self.assertEqual(resp.status_code, 403)

        projects = [
            project_a,
            project_b,
            project_c,
        ]
        for project in projects:
            resp = client.get(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 200)

            resp = client.delete(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 403)

            resp = client.patch(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_project_read_and_write_endpoints_for_staff_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        client.force_authenticate(user=user_admin)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/project/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow creating projects.
        resp = client.post("/api/v2/project/")
        self.assertEqual(resp.status_code, 403)

        projects = [
            project_a,
            project_b,
            project_c,
        ]
        for project in projects:
            resp = client.get(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting projects.
            resp = client.delete(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 403)

            # We don't allow users to update projects.
            resp = client.patch(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_project_read_and_write_endpoints_for_build_api_token(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        _, build_api_key = BuildAPIKey.objects.create_key(project_a)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/project/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow creating projects.
        resp = client.post("/api/v2/project/")
        self.assertEqual(resp.status_code, 405)

        # The key grants access to project_a only.
        resp = client.get(f"/api/v2/project/{project_a.pk}/")
        self.assertEqual(resp.status_code, 200)

        # We don't allow deleting projects.
        resp = client.delete(f"/api/v2/project/{project_a.pk}/")
        self.assertEqual(resp.status_code, 405)

        # Update is fine.
        resp = client.patch(f"/api/v2/project/{project_a.pk}/")
        self.assertEqual(resp.status_code, 200)

        disallowed_projects = [
            project_b,
            project_c,
        ]
        for project in disallowed_projects:
            resp = client.get(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 404)

            resp = client.delete(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 405)

            resp = client.patch(f"/api/v2/project/{project.pk}/")
            self.assertEqual(resp.status_code, 404)

    def test_build_read_only_endpoints_for_normal_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        client.force_authenticate(user=user_normal)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/build/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow creating builds for normal users.
        resp = client.post("/api/v2/build/")
        self.assertEqual(resp.status_code, 403)

        Version.objects.all().update(privacy_level=PUBLIC)

        builds = [
            get(Build, project=project_a, version=project_a.versions.first()),
            get(Build, project=project_b, version=project_b.versions.first()),
            get(Build, project=project_c, version=project_c.versions.first()),
        ]
        for build in builds:
            resp = client.get(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting builds.
            resp = client.delete(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 403)

            # Neither update them.
            resp = client.patch(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_build_read_and_write_endpoints_for_staff_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        client.force_authenticate(user=user_admin)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/build/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow to create builds.
        resp = client.post("/api/v2/build/")
        self.assertEqual(resp.status_code, 403)

        Version.objects.all().update(privacy_level=PUBLIC)

        builds = [
            get(Build, project=project_a, version=project_a.versions.first()),
            get(Build, project=project_b, version=project_b.versions.first()),
            get(Build, project=project_c, version=project_c.versions.first()),
        ]
        for build in builds:
            resp = client.get(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting builds.
            resp = client.delete(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 403)

            # We don't allow users to update them.
            resp = client.patch(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_build_read_and_write_endpoints_for_build_api_token(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        _, build_api_key = BuildAPIKey.objects.create_key(project_a)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/build/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow to create builds.
        resp = client.post("/api/v2/build/")
        self.assertEqual(resp.status_code, 405)

        Version.objects.all().update(privacy_level=PUBLIC)

        # The key grants access to builds form project_a only.
        build = get(Build, project=project_a, version=project_a.versions.first())
        resp = client.get(f"/api/v2/build/{build.pk}/")
        self.assertEqual(resp.status_code, 200)

        # We don't allow deleting builds.
        resp = client.delete(f"/api/v2/build/{build.pk}/")
        self.assertEqual(resp.status_code, 405)

        # Update them is fine.
        resp = client.patch(f"/api/v2/build/{build.pk}/")
        self.assertEqual(resp.status_code, 200)

        disallowed_builds = [
            get(Build, project=project_b, version=project_b.versions.first()),
            get(Build, project=project_c, version=project_c.versions.first()),
        ]
        for build in disallowed_builds:
            resp = client.get(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 404)

            resp = client.delete(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 405)

            resp = client.patch(f"/api/v2/build/{build.pk}/")
            self.assertEqual(resp.status_code, 404)

    def test_build_commands_duplicated_command(self):
        """Sending the same request twice should only create one BuildCommandResult."""
        project = get(
            Project,
            language="en",
        )
        version = project.versions.first()
        build = Build.objects.create(project=project, version=version)

        self.assertEqual(BuildCommandResult.objects.count(), 0)

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        now = timezone.now()
        start_time = now - datetime.timedelta(seconds=5)
        end_time = now

        data = {
            "build": build.pk,
            "command": "git status",
            "description": "Git status",
            "exit_code": 0,
            "start_time": start_time,
            "end_time": end_time,
        }

        response = client.post(
            "/api/v2/command/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        response = client.post(
            "/api/v2/command/",
            data,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(BuildCommandResult.objects.count(), 1)

    def test_build_commands_read_only_endpoints_for_normal_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        client.force_authenticate(user=user_normal)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/build/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow creating commands for normal users.
        resp = client.post("/api/v2/command/")
        self.assertEqual(resp.status_code, 403)

        Version.objects.all().update(privacy_level=PUBLIC)

        builds = [
            get(Build, project=project_a, version=project_a.versions.first()),
            get(Build, project=project_b, version=project_b.versions.first()),
            get(Build, project=project_c, version=project_c.versions.first()),
        ]
        build_commands = [get(BuildCommandResult, build=build) for build in builds]

        for command in build_commands:
            resp = client.get(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting builds.
            resp = client.delete(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 403)

            # Neither update them.
            resp = client.patch(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_build_commands_read_and_write_endpoints_for_staff_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        client.force_authenticate(user=user_admin)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/command/")
        self.assertEqual(resp.status_code, 410)

        Version.objects.all().update(privacy_level=PUBLIC)

        builds = [
            get(Build, project=project_a, version=project_a.versions.first()),
            get(Build, project=project_b, version=project_b.versions.first()),
            get(Build, project=project_c, version=project_c.versions.first()),
        ]
        build_commands = [get(BuildCommandResult, build=build) for build in builds]

        # We don't allow write operations to users.
        resp = client.post(
            "/api/v2/command/",
            {
                "build": builds[0].pk,
                "command": "test",
                "output": "test",
                "exit_code": 0,
                "start_time": datetime.datetime.utcnow(),
                "end_time": datetime.datetime.utcnow(),
            },
        )
        self.assertEqual(resp.status_code, 403)

        for command in build_commands:
            resp = client.get(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting commands.
            resp = client.delete(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 403)

            # Neither updating them.
            resp = client.patch(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_build_commands_read_and_write_endpoints_for_build_api_token(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        client = APIClient()

        _, build_api_key = BuildAPIKey.objects.create_key(project_a)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/command/")
        self.assertEqual(resp.status_code, 410)

        Version.objects.all().update(privacy_level=PUBLIC)

        build = get(Build, project=project_a, version=project_a.versions.first())
        command = get(BuildCommandResult, build=build)

        # We allow creating build commands.
        resp = client.post(
            "/api/v2/command/",
            {
                "build": build.pk,
                "command": "test",
                "output": "test",
                "exit_code": 0,
                "start_time": datetime.datetime.utcnow(),
                "end_time": datetime.datetime.utcnow(),
            },
        )
        self.assertEqual(resp.status_code, 201)

        resp = client.get(f"/api/v2/command/{command.pk}/")
        self.assertEqual(resp.status_code, 200)

        # And updating them.
        resp = client.patch(
            f"/api/v2/command/{command.pk}/",
            {
                "command": "test2",
                "exit_code": 1,
                "output": "test2",
                "end_time": None,
                "start_time": None,
            },
        )
        assert resp.status_code == 200
        command.refresh_from_db()
        assert command.command == "test2"
        assert command.exit_code == 1
        assert command.output == "test2"
        assert command.start_time is None
        assert command.end_time is None

        # Isn't possible to update the build the command belongs to.
        another_build = get(
            Build, project=project_b, version=project_b.versions.first()
        )
        resp = client.patch(
            f"/api/v2/command/{command.pk}/",
            {
                "build": another_build.pk,
            },
        )
        assert resp.status_code == 200
        command.refresh_from_db()
        assert command.build == build

        # We don't allow deleting commands.
        resp = client.delete(f"/api/v2/command/{command.pk}/")
        self.assertEqual(resp.status_code, 405)

        disallowed_builds = [
            get(Build, project=project_b, version=project_b.versions.first()),
            get(Build, project=project_c, version=project_c.versions.first()),
        ]
        disallowed_build_commands = [
            get(BuildCommandResult, build=build) for build in disallowed_builds
        ]
        for command in disallowed_build_commands:
            resp = client.post(
                "/api/v2/command/",
                {
                    "build": command.build.pk,
                    "command": "test",
                    "output": "test",
                    "exit_code": 0,
                    "start_time": datetime.datetime.utcnow(),
                    "end_time": datetime.datetime.utcnow(),
                },
            )
            self.assertEqual(resp.status_code, 403)

            resp = client.get(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 404)

            resp = client.delete(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 405)

            resp = client.patch(f"/api/v2/command/{command.pk}/")
            self.assertEqual(resp.status_code, 404)

    def test_versions_read_only_endpoints_for_normal_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        Version.objects.all().update(privacy_level=PUBLIC)

        client = APIClient()

        client.force_authenticate(user=user_normal)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/version/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow creating versions.
        resp = client.post("/api/v2/version/")
        self.assertEqual(resp.status_code, 403)

        versions = [
            project_a.versions.first(),
            project_b.versions.first(),
            project_c.versions.first(),
        ]

        for version in versions:
            resp = client.get(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting versions.
            resp = client.delete(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 403)

            # Neither update them.
            resp = client.patch(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_versions_read_and_write_endpoints_for_staff_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        Version.objects.all().update(privacy_level=PUBLIC)

        client = APIClient()

        client.force_authenticate(user=user_admin)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/version/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow to create versions.
        resp = client.post("/api/v2/version/")
        self.assertEqual(resp.status_code, 403)

        versions = [
            project_a.versions.first(),
            project_b.versions.first(),
            project_c.versions.first(),
        ]

        for version in versions:
            resp = client.get(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow users to delete versions.
            resp = client.delete(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 403)

            # We don't allow users to update versions.
            resp = client.patch(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_versions_read_and_write_endpoints_for_build_api_token(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        Version.objects.all().update(privacy_level=PUBLIC)

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project_a)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/version/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow to create versions.
        resp = client.post("/api/v2/version/")
        self.assertEqual(resp.status_code, 405)

        version = project_a.versions.first()
        resp = client.get(f"/api/v2/version/{version.pk}/")
        self.assertEqual(resp.status_code, 200)

        # We don't allow deleting versions.
        resp = client.delete(f"/api/v2/version/{version.pk}/")
        self.assertEqual(resp.status_code, 405)

        # Update them is fine.
        resp = client.patch(f"/api/v2/version/{version.pk}/")
        self.assertEqual(resp.status_code, 200)

        disallowed_versions = [
            project_b.versions.first(),
            project_c.versions.first(),
        ]
        for version in disallowed_versions:
            resp = client.get(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 404)

            # We don't allow deleting versions.
            resp = client.delete(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 405)

            # Update them is fine.
            resp = client.patch(f"/api/v2/version/{version.pk}/")
            self.assertEqual(resp.status_code, 404)

    def test_domains_read_only_endpoints_for_normal_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        Version.objects.all().update(privacy_level=PUBLIC)

        client = APIClient()

        client.force_authenticate(user=user_normal)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/domain/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow creating domains.
        resp = client.post("/api/v2/domain/")
        self.assertEqual(resp.status_code, 403)

        domains = [
            get(Domain, project=project_a),
            get(Domain, project=project_b),
            get(Domain, project=project_c),
        ]

        for domain in domains:
            resp = client.get(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting domains.
            resp = client.delete(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 403)

            # Neither update them.
            resp = client.patch(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_domains_read_and_write_endpoints_for_staff_user(self):
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        Version.objects.all().update(privacy_level=PUBLIC)

        client = APIClient()

        client.force_authenticate(user=user_admin)

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/domain/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow to create domains.
        resp = client.post("/api/v2/domain/")
        self.assertEqual(resp.status_code, 403)

        domains = [
            get(Domain, project=project_a),
            get(Domain, project=project_b),
            get(Domain, project=project_c),
        ]

        for domain in domains:
            resp = client.get(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting domains.
            resp = client.delete(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 403)

            # Neither update them.
            resp = client.patch(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_domains_read_and_write_endpoints_for_build_api_token(self):
        # Build API tokens don't grant access to the domain endpoints.
        user_normal = get(User, is_staff=False)
        user_admin = get(User, is_staff=True)

        project_a = get(Project, users=[user_normal], privacy_level=PUBLIC)
        project_b = get(Project, users=[user_admin], privacy_level=PUBLIC)
        project_c = get(Project, privacy_level=PUBLIC)
        Version.objects.all().update(privacy_level=PUBLIC)

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project_a)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        # List operations without a filter aren't allowed.
        resp = client.get("/api/v2/domain/")
        self.assertEqual(resp.status_code, 410)

        # We don't allow to create domains.
        resp = client.post("/api/v2/domain/")
        self.assertEqual(resp.status_code, 403)

        domains = [
            get(Domain, project=project_a),
            get(Domain, project=project_b),
            get(Domain, project=project_c),
        ]
        for domain in domains:
            resp = client.get(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 200)

            # We don't allow deleting domains.
            resp = client.delete(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 403)

            # Neither update them.
            resp = client.patch(f"/api/v2/domain/{domain.pk}/")
            self.assertEqual(resp.status_code, 403)

    def test_project_features(self):
        project = get(Project, main_language_project=None)
        # One explicit, one implicit feature
        feature1 = get(Feature, projects=[project])
        feature2 = get(Feature, projects=[], default_true=True)
        get(Feature, projects=[], default_true=False)

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        resp = client.get("/api/v2/project/%s/" % (project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("features", resp.data)
        self.assertCountEqual(
            resp.data["features"],
            [feature1.feature_id, feature2.feature_id],
        )

    def test_project_features_multiple_projects(self):
        project1 = get(Project, main_language_project=None)
        project2 = get(Project, main_language_project=None)
        feature = get(Feature, projects=[project1, project2], default_true=True)
        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project1)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        resp = client.get("/api/v2/project/%s/" % (project1.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("features", resp.data)
        self.assertEqual(resp.data["features"], [feature.feature_id])

    @mock.patch.object(GitHubAppService, "get_clone_token")
    def test_project_clone_token(self, get_clone_token):
        clone_token = "token:1234"
        get_clone_token.return_value = clone_token
        project = get(Project)

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        # No remote repository, no token.
        assert project.remote_repository is None

        resp = client.get(f"/api/v2/project/{project.pk}/")
        assert resp.status_code == 200
        assert resp.data["clone_token"] == None
        get_clone_token.assert_not_called()

        # Project has a GitHubApp remote repository, but it's public.
        github_app_installation = get(GitHubAppInstallation, installation_id=1234, target_id=1234, target_type=GitHubAccountType.USER)
        remote_repository = get(RemoteRepository, vcs_provider=GitHubAppProvider.id, github_app_installation=github_app_installation, private=False)
        project.remote_repository = remote_repository
        project.save()

        resp = client.get(f"/api/v2/project/{project.pk}/")
        assert resp.status_code == 200
        assert resp.data["clone_token"] == None
        get_clone_token.assert_not_called()

        # Project has a GitHubApp remote repository, and it's private.
        remote_repository.private = True
        remote_repository.save()

        resp = client.get(f"/api/v2/project/{project.pk}/")
        assert resp.status_code == 200
        assert resp.data["clone_token"] == clone_token
        get_clone_token.assert_called_once_with(project)

    def test_remote_repository_pagination(self):
        account = get(SocialAccount, provider="github")
        user = get(User)

        for _ in range(20):
            repo = get(RemoteRepository)
            get(
                RemoteRepositoryRelation,
                remote_repository=repo,
                user=user,
                account=account,
            )

        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get("/api/v2/remote/repo/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 15)  # page_size
        self.assertIn("?page=2", resp.data["next"])

    def test_remote_organization_pagination(self):
        account = get(SocialAccount, provider="github")
        user = get(User)
        for _ in range(30):
            org = get(RemoteOrganization)
            get(
                RemoteOrganizationRelation,
                remote_organization=org,
                user=user,
                account=account,
            )

        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get("/api/v2/remote/org/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 25)  # page_size
        self.assertIn("?page=2", resp.data["next"])

    def test_project_environment_variables(self):
        project = get(Project, main_language_project=None)
        get(
            EnvironmentVariable,
            name="TOKEN",
            value="a1b2c3",
            project=project,
        )

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        resp = client.get("/api/v2/project/%s/" % (project.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("environment_variables", resp.data)
        self.assertEqual(
            resp.data["environment_variables"],
            {"TOKEN": dict(value="a1b2c3", public=False)},
        )

    def test_init_api_project(self):
        project_data = {
            "name": "Test Project",
            "slug": "test-project",
            "show_advertising": True,
        }

        api_project = APIProject(**project_data)
        self.assertEqual(api_project.slug, "test-project")
        self.assertEqual(api_project.features, [])
        self.assertFalse(api_project.ad_free)
        self.assertTrue(api_project.show_advertising)
        self.assertEqual(api_project.environment_variables(public_only=False), {})
        self.assertEqual(api_project.environment_variables(public_only=True), {})

        project_data["features"] = ["test-feature"]
        project_data["show_advertising"] = False
        project_data["environment_variables"] = {
            "TOKEN": dict(value="a1b2c3", public=False),
            "RELEASE": dict(value="prod", public=True),
        }
        api_project = APIProject(**project_data)
        self.assertEqual(api_project.features, ["test-feature"])
        self.assertTrue(api_project.ad_free)
        self.assertFalse(api_project.show_advertising)
        self.assertEqual(
            api_project.environment_variables(public_only=False),
            {"TOKEN": "a1b2c3", "RELEASE": "prod"},
        )
        self.assertEqual(
            api_project.environment_variables(public_only=True),
            {"RELEASE": "prod"},
        )

    def test_invalid_attributes_api_project(self):
        invalid_attribute = "invalid_attribute"
        project_data = {
            "name": "Test Project",
            "slug": "test-project",
            "show_advertising": True,
            invalid_attribute: "nope",
        }
        api_project = APIProject(**project_data)
        self.assertFalse(hasattr(api_project, invalid_attribute))

    def test_invalid_attributes_api_version(self):
        invalid_attribute = "invalid_attribute"
        version_data = {
            "type": "branch",
            "identifier": "main",
            "verbose_name": "main",
            "slug": "v2",
            invalid_attribute: "nope",
        }
        api_version = APIVersion(**version_data)
        self.assertFalse(hasattr(api_version, invalid_attribute))

    @override_settings(
        RTD_DEFAULT_FEATURES=dict(
            [RTDProductFeature(type=TYPE_CONCURRENT_BUILDS, value=4).to_item()]
        ),
    )
    def test_concurrent_builds(self):
        expected = {
            "limit_reached": False,
            "concurrent": 2,
            "max_concurrent": 4,
        }
        project = get(
            Project,
            max_concurrent_builds=None,
            main_language_project=None,
        )
        for state in ("triggered", "building", "cloning", "finished", "cancelled"):
            get(
                Build,
                project=project,
                state=state,
            )

        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        resp = client.get(
            f"/api/v2/build/concurrent/", data={"project__slug": project.slug}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(expected, resp.data)

    def test_add_notification_deduplicated(self):
        project = get(Project)
        build = get(Build, project=project)
        data = {
            "attached_to": f"build/{build.pk}",
            "message_id": BuildMaxConcurrencyError.LIMIT_REACHED,
            "state": READ,
            "dismissable": False,
            "news": False,
            "format_values": {"limit": 10},
        }

        url = "/api/v2/notifications/"

        self.client.logout()

        self.assertEqual(Notification.objects.count(), 0)
        client = APIClient()
        _, build_api_key = BuildAPIKey.objects.create_key(project)
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        response = client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)
        n1 = Notification.objects.first()

        # Adding the same notification, de-duplicates it
        response = client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)
        n2 = Notification.objects.first()

        self.assertEqual(n1.pk, n2.pk)
        self.assertEqual(n1.state, READ)
        self.assertEqual(n2.state, UNREAD)
        self.assertNotEqual(n1.modified, n2.modified)


class APIImportTests(TestCase):

    """Import API endpoint tests."""

    fixtures = ["eric.json", "test_data.json"]

    def test_permissions(self):
        """Ensure user repositories aren't leaked to other users."""
        client = APIClient()

        account_a = get(SocialAccount, provider="github")
        account_b = get(SocialAccount, provider="github")
        account_c = get(SocialAccount, provider="github")
        user_a = get(User, password="test")
        user_b = get(User, password="test")
        user_c = get(User, password="test")
        org_a = get(RemoteOrganization)
        get(
            RemoteOrganizationRelation,
            remote_organization=org_a,
            user=user_a,
            account=account_a,
        )
        repo_a = get(
            RemoteRepository,
            organization=org_a,
        )
        get(
            RemoteRepositoryRelation,
            remote_repository=repo_a,
            user=user_a,
            account=account_a,
        )

        repo_b = get(
            RemoteRepository,
            organization=None,
        )
        get(
            RemoteRepositoryRelation,
            remote_repository=repo_b,
            user=user_b,
            account=account_b,
        )

        client.force_authenticate(user=user_a)
        resp = client.get("/api/v2/remote/repo/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data["results"]
        self.assertEqual(repos[0]["id"], repo_a.id)
        self.assertEqual(repos[0]["organization"]["id"], org_a.id)
        self.assertEqual(len(repos), 1)

        resp = client.get("/api/v2/remote/org/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        orgs = resp.data["results"]
        self.assertEqual(orgs[0]["id"], org_a.id)
        self.assertEqual(len(orgs), 1)

        client.force_authenticate(user=user_b)
        resp = client.get("/api/v2/remote/repo/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data["results"]
        self.assertEqual(repos[0]["id"], repo_b.id)
        self.assertEqual(repos[0]["organization"], None)
        self.assertEqual(len(repos), 1)

        client.force_authenticate(user=user_c)
        resp = client.get("/api/v2/remote/repo/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        repos = resp.data["results"]
        self.assertEqual(len(repos), 0)


@mock.patch("readthedocs.core.views.hooks.trigger_build")
class IntegrationsTests(TestCase):

    """Integration for webhooks, etc."""

    fixtures = ["eric.json", "test_data.json"]

    def setUp(self):
        self.project = get(
            Project,
            build_queue=None,
            external_builds_enabled=True,
            default_branch="master",
        )
        self.version = get(
            Version,
            slug="master",
            verbose_name="master",
            active=True,
            project=self.project,
            type=BRANCH,
        )
        self.version_tag = get(
            Version,
            slug="v1.0",
            verbose_name="v1.0",
            active=True,
            project=self.project,
            type=TAG,
        )
        self.github_payload = {
            "ref": "refs/heads/master",
        }
        self.commit = "ec26de721c3235aad62de7213c562f8c821"
        self.github_pull_request_payload = {
            "action": "opened",
            "number": 2,
            "pull_request": {
                "head": {
                    "sha": self.commit,
                    "ref": "source_branch",
                },
                "base": {
                    "ref": "master",
                },
            },
        }
        self.gitlab_merge_request_payload = {
            "object_kind": GITLAB_MERGE_REQUEST,
            "object_attributes": {
                "iid": "2",
                "last_commit": {"id": self.commit},
                "action": "open",
                "source_branch": "source_branch",
                "target_branch": "master",
            },
        }
        self.gitlab_payload = {
            "object_kind": GITLAB_PUSH,
            "ref": "refs/heads/master",
            "before": "95790bf891e76fee5e1747ab589903a6a1f80f22",
            "after": "95790bf891e76fee5e1747ab589903a6a1f80f23",
        }
        self.bitbucket_payload = {
            "push": {
                "changes": [
                    {
                        "new": {
                            "type": "branch",
                            "name": "master",
                        },
                        "old": {
                            "type": "branch",
                            "name": "master",
                        },
                    }
                ],
            },
        }

        self.github_integration = get(
            Integration,
            project=self.project,
            integration_type=Integration.GITHUB_WEBHOOK,
        )
        self.gitlab_integration = get(
            Integration,
            project=self.project,
            integration_type=Integration.GITLAB_WEBHOOK,
        )
        self.bitbucket_integration = get(
            Integration,
            project=self.project,
            integration_type=Integration.BITBUCKET_WEBHOOK,
        )
        self.generic_integration = get(
            GenericAPIWebhook,
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

    def test_webhook_skipped_project(self, trigger_build):
        client = APIClient()
        self.project.skip = True
        self.project.save()

        response = client.post(
            "/api/v2/webhook/github/{}/".format(
                self.project.slug,
            ),
            self.github_payload,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: get_signature(
                    self.github_integration, self.github_payload
                ),
            },
        )
        self.assertDictEqual(
            response.data, {"detail": "This project is currently disabled"}
        )
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertFalse(trigger_build.called)

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_sync_repository_custom_project_queue(
        self, sync_repository_task, trigger_build
    ):
        """
        Check that the custom queue is used for sync_repository_task.
        """
        client = APIClient()
        self.project.build_queue = "specific-build-queue"
        self.project.save()

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_CREATE,
            GITHUB_SIGNATURE_HEADER: get_signature(
                self.github_integration, self.github_payload
            ),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            self.github_payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        self.assertTrue(resp.data["versions_synced"])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[
                latest_version.pk,
            ],
            kwargs={
                "build_api_key": mock.ANY,
            },
            queue="specific-build-queue",
        )

    def test_github_webhook_for_branches(self, trigger_build):
        """GitHub webhook API."""
        client = APIClient()

        data = {"ref": "refs/heads/master"}
        client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            data,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, data),
            },
        )
        trigger_build.assert_has_calls(
            [mock.call(version=self.version, project=self.project)],
        )

        data = {"ref": "refs/heads/non-existent"}
        client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            data,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, data),
            },
        )
        trigger_build.assert_has_calls(
            [mock.call(version=mock.ANY, project=self.project)],
        )

        data = {"ref": "refs/heads/master"}
        client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            data,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, data),
            },
        )
        trigger_build.assert_has_calls(
            [mock.call(version=self.version, project=self.project)],
        )

    def test_github_webhook_for_tags(self, trigger_build):
        """GitHub webhook API."""
        client = APIClient()
        data = {"ref": "refs/tags/v1.0"}

        client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            data,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, data),
            },
        )
        trigger_build.assert_has_calls(
            [mock.call(version=self.version_tag, project=self.project)],
        )

        data = {"ref": "refs/heads/non-existent"}
        client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            data,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, data),
            },
        )
        trigger_build.assert_has_calls(
            [mock.call(version=mock.ANY, project=self.project)],
        )

        data = {"ref": "refs/tags/v1.0"}
        client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            data,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, data),
            },
        )
        trigger_build.assert_has_calls(
            [mock.call(version=self.version_tag, project=self.project)],
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_github_webhook_no_build_on_delete(
        self, sync_repository_task, trigger_build
    ):
        client = APIClient()

        payload = {"ref": "master", "deleted": True}
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, payload),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_github_ping_event(self, sync_repository_task, trigger_build):
        client = APIClient()

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PING,
            GITHUB_SIGNATURE_HEADER: get_signature(
                self.github_integration, self.github_payload
            ),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            self.github_payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.data, {"detail": "Webhook configured correctly"})
        trigger_build.assert_not_called()
        sync_repository_task.assert_not_called()

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_github_create_event(self, sync_repository_task, trigger_build):
        client = APIClient()

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_CREATE,
            GITHUB_SIGNATURE_HEADER: get_signature(
                self.github_integration, self.github_payload
            ),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            self.github_payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_github_pull_request_opened_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST,
            GITHUB_SIGNATURE_HEADER: get_signature(
                self.github_integration, self.github_pull_request_payload
            ),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            self.github_pull_request_payload,
            format="json",
            headers=headers,
        )
        # get the created external version
        external_version = self.project.versions(manager=EXTERNAL).get(verbose_name="2")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            project=self.project, version=external_version, commit=self.commit
        )
        self.assertTrue(external_version)

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_github_pull_request_reopened_event(
        self, trigger_build, core_trigger_build
    ):
        client = APIClient()

        # Update the payload for `reopened` webhook event
        pull_request_number = "5"
        payload = self.github_pull_request_payload
        payload["action"] = GITHUB_PULL_REQUEST_REOPENED
        payload["number"] = pull_request_number

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST,
            GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, payload),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            payload,
            format="json",
            headers=headers,
        )
        # get the created external version
        external_version = self.project.versions(manager=EXTERNAL).get(
            verbose_name=pull_request_number
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            project=self.project, version=external_version, commit=self.commit
        )
        self.assertTrue(external_version)

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_github_pull_request_synchronize_event(
        self, trigger_build, core_trigger_build
    ):
        client = APIClient()

        pull_request_number = "6"
        prev_identifier = "95790bf891e76fee5e1747ab589903a6a1f80f23"
        # create an existing external version for pull request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=pull_request_number,
            identifier=prev_identifier,
        )

        # Update the payload for `synchronize` webhook event
        payload = self.github_pull_request_payload
        payload["action"] = GITHUB_PULL_REQUEST_SYNC
        payload["number"] = pull_request_number

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST,
            GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, payload),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            payload,
            format="json",
            headers=headers,
        )
        # get updated external version
        external_version = self.project.versions(manager=EXTERNAL).get(
            verbose_name=pull_request_number
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            project=self.project, version=external_version, commit=self.commit
        )
        # `synchronize` webhook event updated the identifier (commit hash)
        self.assertNotEqual(prev_identifier, external_version.identifier)

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_github_pull_request_closed_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        pull_request_number = "7"
        identifier = "95790bf891e76fee5e1747ab589903a6a1f80f23"
        # create an existing external version for pull request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=pull_request_number,
            identifier=identifier,
        )

        # Update the payload for `closed` webhook event
        payload = self.github_pull_request_payload
        payload["action"] = GITHUB_PULL_REQUEST_CLOSED
        payload["number"] = pull_request_number
        payload["pull_request"]["head"]["sha"] = identifier

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST,
            GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, payload),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            payload,
            format="json",
            headers=headers,
        )
        external_version = self.project.versions(manager=EXTERNAL).get(
            verbose_name=pull_request_number
        )

        self.assertTrue(external_version.active)
        self.assertEqual(external_version.state, EXTERNAL_VERSION_STATE_CLOSED)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["closed"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [version.verbose_name])
        core_trigger_build.assert_not_called()

    def test_github_pull_request_no_action(self, trigger_build):
        client = APIClient()

        payload = {
            "number": 2,
            "pull_request": {"head": {"sha": "ec26de721c3235aad62de7213c562f8c821"}},
        }
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST,
            GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, payload),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["detail"], "Unhandled webhook event")

    def test_github_pull_request_opened_event_invalid_payload(self, trigger_build):
        client = APIClient()

        payload = {
            "action": GITHUB_PULL_REQUEST_OPENED,
            "number": 2,
        }
        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            payload,
            format="json",
            headers=headers,
        )

        self.assertEqual(resp.status_code, 400)

    def test_github_pull_request_closed_event_invalid_payload(self, trigger_build):
        client = APIClient()

        payload = {
            "action": GITHUB_PULL_REQUEST_CLOSED,
            "number": 2,
        }
        headers = {GITHUB_EVENT_HEADER: GITHUB_PULL_REQUEST}
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            payload,
            format="json",
            headers=headers,
        )

        self.assertEqual(resp.status_code, 400)

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_github_delete_event(self, sync_repository_task, trigger_build):
        client = APIClient()

        headers = {
            GITHUB_EVENT_HEADER: GITHUB_DELETE,
            GITHUB_SIGNATURE_HEADER: get_signature(
                self.github_integration, self.github_payload
            ),
        }
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            self.github_payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    def test_github_parse_ref(self, trigger_build):
        self.assertEqual(
            parse_version_from_ref("refs/heads/master"), ("master", BRANCH)
        )
        self.assertEqual(parse_version_from_ref("refs/heads/v0.1"), ("v0.1", BRANCH))
        self.assertEqual(parse_version_from_ref("refs/tags/v0.1"), ("v0.1", TAG))
        self.assertEqual(parse_version_from_ref("refs/tags/tag"), ("tag", TAG))
        self.assertEqual(
            parse_version_from_ref("refs/heads/stable/2018"), ("stable/2018", BRANCH)
        )
        self.assertEqual(
            parse_version_from_ref("refs/tags/tag/v0.1"), ("tag/v0.1", TAG)
        )

    def test_github_invalid_webhook(self, trigger_build):
        """GitHub webhook unhandled event."""
        client = APIClient()
        payload = {"foo": "bar"}
        resp = client.post(
            "/api/v2/webhook/github/{}/".format(self.project.slug),
            payload,
            format="json",
            headers={
                GITHUB_EVENT_HEADER: "issues",
                GITHUB_SIGNATURE_HEADER: get_signature(
                    self.github_integration, payload
                ),
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["detail"], "Unhandled webhook event")

    def test_github_invalid_payload(self, trigger_build):
        client = APIClient()
        wrong_signature = "1234"
        self.assertNotEqual(self.github_integration.secret, wrong_signature)
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: wrong_signature,
        }
        resp = client.post(
            reverse("api_webhook_github", kwargs={"project_slug": self.project.slug}),
            self.github_payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["detail"], GitHubWebhookView.invalid_payload_msg)

    def test_github_valid_payload(self, trigger_build):
        client = APIClient()
        payload = '{"ref":"refs/heads/master"}'
        signature = get_signature(
            self.github_integration,
            payload,
        )
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: signature,
        }
        resp = client.post(
            reverse("api_webhook_github", kwargs={"project_slug": self.project.slug}),
            json.loads(payload),
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, 200)

    def test_github_empty_signature(self, trigger_build):
        client = APIClient()
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: "",
        }
        resp = client.post(
            reverse("api_webhook_github", kwargs={"project_slug": self.project.slug}),
            self.github_payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["detail"], GitHubWebhookView.invalid_payload_msg)

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task", mock.MagicMock())
    def test_github_sync_on_push_event(self, trigger_build):
        """Sync if the webhook doesn't have the create/delete events, but we receive a push event with created/deleted."""
        self.github_integration.provider_data = {
            "events": [],
        }
        self.github_integration.save()

        client = APIClient()

        payload = {
            "ref": "master",
            "created": True,
            "deleted": False,
        }
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, payload),
        }
        resp = client.post(
            reverse("api_webhook_github", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
            headers=headers,
        )
        self.assertTrue(resp.json()["versions_synced"])

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task", mock.MagicMock())
    def test_github_dont_trigger_double_sync(self, trigger_build):
        """Don't trigger a sync twice if the webhook has the create/delete events."""
        self.github_integration.provider_data = {
            "events": [
                GITHUB_CREATE,
                GITHUB_DELETE,
            ],
        }
        self.github_integration.save()

        client = APIClient()

        payload = {
            "ref": "master",
            "created": True,
            "deleted": False,
        }
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, payload),
        }
        resp = client.post(
            reverse("api_webhook_github", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
            headers=headers,
        )
        self.assertFalse(resp.json()["versions_synced"])

        payload = {"ref": "master"}
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_CREATE,
            GITHUB_SIGNATURE_HEADER: get_signature(self.github_integration, payload),
        }
        resp = client.post(
            reverse("api_webhook_github", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
            headers=headers,
        )
        self.assertTrue(resp.json()["versions_synced"])

    def test_github_get_external_version_data(self, trigger_build):
        view = GitHubWebhookView(data=self.github_pull_request_payload)
        version_data = view.get_external_version_data()
        self.assertEqual(version_data.id, "2")
        self.assertEqual(version_data.commit, self.commit)
        self.assertEqual(version_data.source_branch, "source_branch")
        self.assertEqual(version_data.base_branch, "master")

    def test_github_skip_githubapp_projects(self, trigger_build):
        installation = get(
            GitHubAppInstallation,
            installation_id=1111,
            target_id=1111,
            target_type=GitHubAccountType.USER,
        )
        remote_repository = get(
            RemoteRepository,
            remote_id="1234",
            name="repo",
            full_name="user/repo",
            vcs_provider=GitHubAppProvider.id,
            github_app_installation=installation,
        )
        self.project.remote_repository = remote_repository
        self.project.save()

        assert self.project.is_github_app_project
        assert self.project.notifications.count() == 0

        client = APIClient()
        payload = '{"ref":"refs/heads/master"}'
        signature = get_signature(
            self.github_integration,
            payload,
        )
        headers = {
            GITHUB_EVENT_HEADER: GITHUB_PUSH,
            GITHUB_SIGNATURE_HEADER: signature,
        }
        resp = client.post(
            reverse("api_webhook_github", kwargs={"project_slug": self.project.slug}),
            json.loads(payload),
            format="json",
            headers=headers,
        )
        assert resp.status_code == 400
        assert "This project is connected to our GitHub App" in resp.data["detail"]

        notification = self.project.notifications.first()
        assert notification is not None
        assert notification.message_id == MESSAGE_PROJECT_DEPRECATED_WEBHOOK

    def test_gitlab_webhook_for_branches(self, trigger_build):
        """GitLab webhook API."""
        client = APIClient()
        headers = {
            GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
        }
        client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
            headers=headers,
        )
        trigger_build.assert_called_with(
            version=mock.ANY,
            project=self.project,
        )

        trigger_build.reset_mock()
        self.gitlab_payload.update(
            ref="non-existent",
        )
        client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
        )
        trigger_build.assert_not_called()

    def test_gitlab_webhook_for_tags(self, trigger_build):
        client = APIClient()
        self.gitlab_payload.update(
            object_kind=GITLAB_TAG_PUSH,
            ref="refs/tags/v1.0",
        )
        headers = {
            GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
        }
        client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
            headers=headers,
        )
        trigger_build.assert_called_with(
            version=self.version_tag,
            project=self.project,
        )

        trigger_build.reset_mock()
        self.gitlab_payload.update(
            ref="refs/tags/v1.0",
        )
        client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
            headers=headers,
        )
        trigger_build.assert_called_with(
            version=self.version_tag,
            project=self.project,
        )

        trigger_build.reset_mock()
        self.gitlab_payload.update(
            ref="refs/heads/non-existent",
        )
        client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
            headers=headers,
        )
        trigger_build.assert_not_called()

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_gitlab_push_hook_creation(
        self,
        sync_repository_task,
        trigger_build,
    ):
        client = APIClient()
        self.gitlab_payload.update(
            before=GITLAB_NULL_HASH,
            after="95790bf891e76fee5e1747ab589903a6a1f80f22",
        )
        resp = client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_gitlab_push_hook_deletion(
        self,
        sync_repository_task,
        trigger_build,
    ):
        client = APIClient()
        self.gitlab_payload.update(
            before="95790bf891e76fee5e1747ab589903a6a1f80f22",
            after=GITLAB_NULL_HASH,
        )
        resp = client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_gitlab_tag_push_hook_creation(
        self,
        sync_repository_task,
        trigger_build,
    ):
        client = APIClient()
        self.gitlab_payload.update(
            object_kind=GITLAB_TAG_PUSH,
            before=GITLAB_NULL_HASH,
            after="95790bf891e76fee5e1747ab589903a6a1f80f22",
        )
        resp = client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_gitlab_tag_push_hook_deletion(
        self,
        sync_repository_task,
        trigger_build,
    ):
        client = APIClient()
        self.gitlab_payload.update(
            object_kind=GITLAB_TAG_PUSH,
            before="95790bf891e76fee5e1747ab589903a6a1f80f22",
            after=GITLAB_NULL_HASH,
        )
        resp = client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            self.gitlab_payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    def test_gitlab_invalid_webhook(self, trigger_build):
        """GitLab webhook unhandled event."""
        client = APIClient()
        resp = client.post(
            "/api/v2/webhook/gitlab/{}/".format(self.project.slug),
            {"object_kind": "pull_request"},
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["detail"], "Unhandled webhook event")

    def test_gitlab_invalid_payload(self, trigger_build):
        client = APIClient()
        wrong_secret = "1234"
        self.assertNotEqual(self.gitlab_integration.secret, wrong_secret)
        headers = {
            GITLAB_TOKEN_HEADER: wrong_secret,
        }
        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            self.gitlab_payload,
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["detail"], GitLabWebhookView.invalid_payload_msg)

    def test_gitlab_valid_payload(self, trigger_build):
        client = APIClient()
        headers = {
            GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
        }
        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            {"object_kind": "pull_request"},
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, 200)

    def test_gitlab_empty_token(self, trigger_build):
        client = APIClient()
        headers = {
            GITLAB_TOKEN_HEADER: "",
        }
        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            {"object_kind": "pull_request"},
            format="json",
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["detail"], GitLabWebhookView.invalid_payload_msg)

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_gitlab_merge_request_open_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            self.gitlab_merge_request_payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        # get the created external version
        external_version = self.project.versions(manager=EXTERNAL).get(verbose_name="2")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            project=self.project, version=external_version, commit=self.commit
        )
        self.assertTrue(external_version)

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_gitlab_merge_request_reopen_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        # Update the payload for `reopen` webhook event
        merge_request_number = "5"
        payload = self.gitlab_merge_request_payload
        payload["object_attributes"]["action"] = GITLAB_MERGE_REQUEST_REOPEN
        payload["object_attributes"]["iid"] = merge_request_number

        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        # get the created external version
        external_version = self.project.versions(manager=EXTERNAL).get(
            verbose_name=merge_request_number
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            project=self.project, version=external_version, commit=self.commit
        )
        self.assertTrue(external_version)

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_gitlab_merge_request_update_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        merge_request_number = "6"
        prev_identifier = "95790bf891e76fee5e1747ab589903a6a1f80f23"
        # create an existing external version for merge request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=merge_request_number,
            identifier=prev_identifier,
        )

        # Update the payload for merge request `update` webhook event
        payload = self.gitlab_merge_request_payload
        payload["object_attributes"]["action"] = GITLAB_MERGE_REQUEST_UPDATE
        payload["object_attributes"]["iid"] = merge_request_number

        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        # get updated external version
        external_version = self.project.versions(manager=EXTERNAL).get(
            verbose_name=merge_request_number
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [external_version.verbose_name])
        core_trigger_build.assert_called_once_with(
            project=self.project, version=external_version, commit=self.commit
        )
        # `update` webhook event updated the identifier (commit hash)
        self.assertNotEqual(prev_identifier, external_version.identifier)

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_gitlab_merge_request_close_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        merge_request_number = "7"
        identifier = "95790bf891e76fee5e1747ab589903a6a1f80f23"
        # create an existing external version for merge request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=merge_request_number,
            identifier=identifier,
        )

        # Update the payload for `closed` webhook event
        payload = self.gitlab_merge_request_payload
        payload["object_attributes"]["action"] = GITLAB_MERGE_REQUEST_CLOSE
        payload["object_attributes"]["iid"] = merge_request_number
        payload["object_attributes"]["last_commit"]["id"] = identifier

        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        external_version = self.project.versions(manager=EXTERNAL).get(
            verbose_name=merge_request_number
        )

        self.assertTrue(external_version.active)
        self.assertEqual(external_version.state, EXTERNAL_VERSION_STATE_CLOSED)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["closed"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [version.verbose_name])
        core_trigger_build.assert_not_called()

    @mock.patch("readthedocs.core.utils.trigger_build")
    def test_gitlab_merge_request_merge_event(self, trigger_build, core_trigger_build):
        client = APIClient()

        merge_request_number = "8"
        identifier = "95790bf891e76fee5e1747ab589903a6a1f80f23"
        # create an existing external version for merge request
        version = get(
            Version,
            project=self.project,
            type=EXTERNAL,
            built=True,
            uploaded=True,
            active=True,
            verbose_name=merge_request_number,
            identifier=identifier,
        )

        # Update the payload for `merge` webhook event
        payload = self.gitlab_merge_request_payload
        payload["object_attributes"]["action"] = GITLAB_MERGE_REQUEST_MERGE
        payload["object_attributes"]["iid"] = merge_request_number
        payload["object_attributes"]["last_commit"]["id"] = identifier

        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        external_version = self.project.versions(manager=EXTERNAL).get(
            verbose_name=merge_request_number
        )

        # external version should be deleted
        self.assertTrue(external_version.active)
        self.assertEqual(external_version.state, EXTERNAL_VERSION_STATE_CLOSED)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["closed"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [version.verbose_name])
        core_trigger_build.assert_not_called()

    def test_gitlab_merge_request_no_action(self, trigger_build):
        client = APIClient()

        payload = {
            "object_kind": GITLAB_MERGE_REQUEST,
            "object_attributes": {
                "iid": 2,
                "last_commit": {"id": self.commit},
            },
        }

        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
            headers={
                GITLAB_TOKEN_HEADER: self.gitlab_integration.secret,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["detail"], "Unhandled webhook event")

    def test_gitlab_merge_request_open_event_invalid_payload(self, trigger_build):
        client = APIClient()

        payload = {
            "object_kind": GITLAB_MERGE_REQUEST,
            "object_attributes": {"action": GITLAB_MERGE_REQUEST_CLOSE},
        }
        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_gitlab_merge_request_close_event_invalid_payload(self, trigger_build):
        client = APIClient()

        payload = {
            "object_kind": GITLAB_MERGE_REQUEST,
            "object_attributes": {"action": GITLAB_MERGE_REQUEST_CLOSE},
        }

        resp = client.post(
            reverse("api_webhook_gitlab", kwargs={"project_slug": self.project.slug}),
            payload,
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_gitlab_get_external_version_data(self, trigger_build):
        view = GitLabWebhookView(data=self.gitlab_merge_request_payload)
        version_data = view.get_external_version_data()
        self.assertEqual(version_data.id, "2")
        self.assertEqual(version_data.commit, self.commit)
        self.assertEqual(version_data.source_branch, "source_branch")
        self.assertEqual(version_data.base_branch, "master")

    def test_bitbucket_webhook(self, trigger_build):
        """Bitbucket webhook API."""
        client = APIClient()
        client.post(
            "/api/v2/webhook/bitbucket/{}/".format(self.project.slug),
            self.bitbucket_payload,
            format="json",
            headers={
                BITBUCKET_SIGNATURE_HEADER: get_signature(
                    self.bitbucket_integration, self.bitbucket_payload
                ),
            },
        )
        trigger_build.assert_has_calls(
            [mock.call(version=mock.ANY, project=self.project)],
        )
        client.post(
            "/api/v2/webhook/bitbucket/{}/".format(self.project.slug),
            {
                "push": {
                    "changes": [
                        {
                            "new": {"name": "non-existent"},
                            "old": {"name": "master"},
                        },
                    ],
                },
            },
            format="json",
        )
        trigger_build.assert_has_calls(
            [mock.call(version=mock.ANY, project=self.project)],
        )

        trigger_build_call_count = trigger_build.call_count
        client.post(
            "/api/v2/webhook/bitbucket/{}/".format(self.project.slug),
            {
                "push": {
                    "changes": [
                        {
                            "new": None,
                        },
                    ],
                },
            },
            format="json",
        )
        self.assertEqual(trigger_build_call_count, trigger_build.call_count)

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_bitbucket_push_hook_creation(
        self,
        sync_repository_task,
        trigger_build,
    ):
        client = APIClient()
        self.bitbucket_payload["push"]["changes"][0]["old"] = None
        resp = client.post(
            "/api/v2/webhook/bitbucket/{}/".format(self.project.slug),
            self.bitbucket_payload,
            format="json",
            headers={
                BITBUCKET_SIGNATURE_HEADER: get_signature(
                    self.bitbucket_integration, self.bitbucket_payload
                ),
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_bitbucket_push_hook_deletion(
        self,
        sync_repository_task,
        trigger_build,
    ):
        client = APIClient()
        self.bitbucket_payload["push"]["changes"][0]["new"] = None
        resp = client.post(
            "/api/v2/webhook/bitbucket/{}/".format(self.project.slug),
            self.bitbucket_payload,
            format="json",
            headers={
                BITBUCKET_SIGNATURE_HEADER: get_signature(
                    self.bitbucket_integration, self.bitbucket_payload
                ),
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["build_triggered"])
        self.assertEqual(resp.data["project"], self.project.slug)
        self.assertEqual(resp.data["versions"], [LATEST])
        trigger_build.assert_not_called()
        latest_version = self.project.versions.get(slug=LATEST)
        sync_repository_task.apply_async.assert_called_with(
            args=[latest_version.pk], kwargs={"build_api_key": mock.ANY}
        )

    def test_bitbucket_invalid_webhook(self, trigger_build):
        """Bitbucket webhook unhandled event."""
        client = APIClient()
        payload = {"foo": "bar"}
        resp = client.post(
            "/api/v2/webhook/bitbucket/{}/".format(self.project.slug),
            payload,
            format="json",
            headers={
                BITBUCKET_EVENT_HEADER: "pull_request",
                BITBUCKET_SIGNATURE_HEADER: get_signature(
                    self.bitbucket_integration, payload
                ),
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["detail"], "Unhandled webhook event")

    def test_generic_api_fails_without_auth(self, trigger_build):
        client = APIClient()
        resp = client.post(
            "/api/v2/webhook/generic/{}/".format(self.project.slug),
            {},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.data["detail"],
            "Authentication credentials were not provided.",
        )

    def test_generic_api_respects_token_auth(self, trigger_build):
        client = APIClient()
        self.assertIsNotNone(self.generic_integration.token)
        resp = client.post(
            "/api/v2/webhook/{}/{}/".format(
                self.project.slug,
                self.generic_integration.pk,
            ),
            {"token": self.generic_integration.token},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["build_triggered"])
        # Test nonexistent branch
        resp = client.post(
            "/api/v2/webhook/{}/{}/".format(
                self.project.slug,
                self.generic_integration.pk,
            ),
            {"token": self.generic_integration.token, "branches": "nonexistent"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["build_triggered"])

    def test_generic_api_respects_basic_auth(self, trigger_build):
        client = APIClient()
        user = get(User)
        self.project.users.add(user)
        client.force_authenticate(user=user)
        resp = client.post(
            "/api/v2/webhook/generic/{}/".format(self.project.slug),
            {},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["build_triggered"])

    def test_generic_api_falls_back_to_token_auth(self, trigger_build):
        client = APIClient()
        user = get(User)
        client.force_authenticate(user=user)
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )
        self.assertIsNotNone(integration.token)
        resp = client.post(
            "/api/v2/webhook/{}/{}/".format(
                self.project.slug,
                integration.pk,
            ),
            {"token": integration.token},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["build_triggered"])

    def test_webhook_doesnt_build_latest_if_is_deactivated(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

        latest_version = self.project.versions.get(slug=LATEST)
        latest_version.active = False
        latest_version.save()

        default_branch = self.project.versions.get(slug="master")
        default_branch.active = False
        default_branch.save()

        resp = client.post(
            "/api/v2/webhook/{}/{}/".format(
                self.project.slug,
                integration.pk,
            ),
            {"token": integration.token, "branches": default_branch.slug},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["build_triggered"])
        trigger_build.assert_not_called()

    def test_webhook_builds_only_master(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

        latest_version = self.project.versions.get(slug=LATEST)
        latest_version.active = False
        latest_version.save()

        default_branch = self.project.versions.get(slug="master")

        self.assertFalse(latest_version.active)
        self.assertTrue(default_branch.active)

        resp = client.post(
            "/api/v2/webhook/{}/{}/".format(
                self.project.slug,
                integration.pk,
            ),
            {"token": integration.token, "branches": default_branch.slug},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(resp.data["versions"], ["master"])

    def test_webhook_build_latest_and_master(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

        latest_version = self.project.versions.get(slug=LATEST)
        default_branch = self.project.versions.get(slug="master")

        self.assertTrue(latest_version.active)
        self.assertTrue(default_branch.active)

        resp = client.post(
            "/api/v2/webhook/{}/{}/".format(
                self.project.slug,
                integration.pk,
            ),
            {
                "token": integration.token,
                "branches": default_branch.slug,
                "default_branch": "master",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(set(resp.data["versions"]), {"latest", "master"})

    def test_webhook_build_another_branch(self, trigger_build):
        client = APIClient()
        integration = Integration.objects.create(
            project=self.project,
            integration_type=Integration.API_WEBHOOK,
        )

        version_v1 = self.project.versions.get(slug="v1.0")

        self.assertTrue(version_v1.active)

        resp = client.post(
            "/api/v2/webhook/{}/{}/".format(
                self.project.slug,
                integration.pk,
            ),
            {"token": integration.token, "branches": version_v1.slug},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["build_triggered"])
        self.assertEqual(resp.data["versions"], ["v1.0"])

    def test_dont_allow_webhooks_without_a_secret(self, trigger_build):
        client = APIClient()

        Integration.objects.filter(pk=self.github_integration.pk).update(secret=None)
        resp = client.post(
            f"/api/v2/webhook/github/{self.project.slug}/",
            self.github_payload,
            format="json",
            headers={GITHUB_SIGNATURE_HEADER: "skip"},
        )
        self.assertContains(
            resp, "This webhook doesn't have a secret configured.", status_code=400
        )

        self.generic_integration.provider_data = {"token": None}
        self.generic_integration.save()
        resp = client.post(
            f"/api/v2/webhook/{self.project.slug}/{self.generic_integration.pk}/",
            {"token": "skip"},
            format="json",
        )
        # For generic webhooks, we first check if the secret matches,
        # and return a 400 if it doesn't.
        self.assertEqual(resp.status_code, 404)

    def test_multiple_integrations_error(self, trigger_build):
        """Test that multiple integrations with same type returns a 400 error."""
        client = APIClient()

        # Create a second GitHub integration for the same project with the same secret
        secret = self.github_integration.secret
        Integration.objects.create(
            project=self.project,
            integration_type=Integration.GITHUB_WEBHOOK,
            secret=secret,
        )

        # Now there are two integrations, so the webhook should return a 400 error
        payload = {"ref": "refs/heads/master"}
        signature = get_signature(self.github_integration, payload)

        resp = client.post(
            f"/api/v2/webhook/github/{self.project.slug}/",
            payload,
            format="json",
            headers={
                GITHUB_SIGNATURE_HEADER: signature,
            },
        )

        # Should return 400 Bad Request
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Multiple integrations found", resp.data["detail"])


@override_settings(PUBLIC_DOMAIN="readthedocs.io")
class APIVersionTests(TestCase):
    fixtures = ["eric", "test_data"]
    maxDiff = None  # So we get an actual diff when it fails

    def test_get_version_by_id(self):
        """
        Test the full response of ``/api/v2/version/{pk}`` is what we expects.

        Allows us to notice changes in the fields returned by the endpoint
        instead of let them pass silently.
        """
        pip = Project.objects.get(slug="pip")
        version = pip.versions.get(slug="0.8")
        _, build_api_key = BuildAPIKey.objects.create_key(pip)

        data = {
            "pk": version.pk,
        }
        resp = self.client.get(
            reverse("version-detail", kwargs=data),
            content_type="application/json",
            headers={"authorization": f"Token {build_api_key}"},
        )
        self.assertEqual(resp.status_code, 200)

        version_data = {
            "type": "tag",
            "verbose_name": "0.8",
            "built": False,
            "id": 18,
            "active": True,
            "canonical_url": "http://pip.readthedocs.io/en/0.8/",
            "project": {
                "analytics_code": None,
                "analytics_disabled": False,
                "canonical_url": "http://pip.readthedocs.io/en/latest/",
                "cdn_enabled": False,
                "container_image": None,
                "container_mem_limit": None,
                "container_time_limit": None,
                "default_branch": None,
                "default_version": "latest",
                "description": "",
                "documentation_type": "sphinx",
                "environment_variables": {},
                "features": [],
                "git_checkout_command": None,
                "has_valid_clone": False,
                "has_valid_webhook": False,
                "id": 6,
                "language": "en",
                "max_concurrent_builds": None,
                "name": "Pip",
                "programming_language": "words",
                "repo": "https://github.com/pypa/pip",
                "repo_type": "git",
                "readthedocs_yaml_path": None,
                "show_advertising": True,
                "skip": False,
                "slug": "pip",
                "users": [1],
                "custom_prefix": None,
                "clone_token": None,
                "has_ssh_key_with_write_access": False,
            },
            "privacy_level": "public",
            "downloads": {},
            "identifier": "2404a34eba4ee9c48cc8bc4055b99a48354f4950",
            "git_identifier": "0.8",
            "slug": "0.8",
            "has_epub": False,
            "has_htmlzip": False,
            "has_pdf": False,
            "documentation_type": "sphinx",
            "machine": False,
        }

        self.assertDictEqual(
            resp.data,
            version_data,
        )

    def test_get_active_versions(self):
        """Test the full response of
        ``/api/v2/version/?project__slug=pip&active=true``"""
        pip = Project.objects.get(slug="pip")
        get(Version, project=pip, active=False, privacy_level=PUBLIC)

        data = {
            "project__slug": pip.slug,
            "active": "true",
        }
        url = reverse("version-list")
        with self.assertNumQueries(5):
            resp = self.client.get(url, data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], pip.versions.filter(active=True).count())

        # Do the same thing for inactive versions
        data.update(
            {
                "active": "false",
            }
        )
        with self.assertNumQueries(5):
            resp = self.client.get(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], pip.versions.filter(active=False).count())

    def test_listing_of_versions_without_filtering_by_a_project(self):
        url = reverse("version-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 410)

        data = {
            "active": "true",
        }
        resp = self.client.get(url, data)
        self.assertEqual(resp.status_code, 410)

        data["project__slug"] = ""
        resp = self.client.get(url, data)
        self.assertEqual(resp.status_code, 410)

        data["project__slug"] = " \n"
        resp = self.client.get(url, data)
        self.assertEqual(resp.status_code, 410)

    def test_project_get_active_versions(self):
        pip = Project.objects.get(slug="pip")
        url = reverse("project-active-versions", args=[pip.pk])
        with self.assertNumQueries(5):
            resp = self.client.get(url)
        self.assertEqual(
            len(resp.data["versions"]), pip.versions.filter(active=True).count()
        )

    def test_modify_version(self):
        pip = Project.objects.get(slug="pip")
        version = pip.versions.get(slug="0.8")
        _, build_api_key = BuildAPIKey.objects.create_key(pip)

        data = {
            "pk": version.pk,
        }
        resp = self.client.patch(
            reverse("version-detail", kwargs=data),
            data=json.dumps({"built": False, "has_pdf": True}),
            content_type="application/json",
            headers={"authorization": f"Token {build_api_key}"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["built"], False)
        self.assertEqual(resp.data["has_pdf"], True)
        self.assertEqual(resp.data["has_epub"], False)
        self.assertEqual(resp.data["has_htmlzip"], False)
