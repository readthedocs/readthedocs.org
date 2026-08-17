from unittest import mock

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import BUILD_STATE_BUILDING
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.doc_builder.exceptions import BuildMaxConcurrencyError
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.notifications.models import Notification
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project
from readthedocs.upload.api.serializers import UploadStatus


class UploadAPIEndpointMixin(TestCase):
    def setUp(self):
        self.user = fixture.get(
            User,
            username="testuser",
        )
        self.token = fixture.get(Token, key="me", user=self.user)

        self.project = fixture.get(
            Project,
            slug="project",
            related_projects=[],
            main_language_project=None,
            users=[self.user],
            versions=[],
        )
        self.feature = fixture.get(
            Feature,
            feature_id=Feature.ALLOW_DIRECT_ARTIFACTS_UPLOAD,
            projects=[self.project],
        )

        self.other_user = fixture.get(User, username="otheruser")

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def tearDown(self):
        # Cleanup cache to avoid throttling on tests.
        cache.clear()


@override_settings(ALLOW_PRIVATE_REPOS=False)
class UploadInitiateViewTests(UploadAPIEndpointMixin):
    def setUp(self):
        super().setUp()
        self.url = reverse("upload-api-initiate")
        self.data = {
            "project": self.project.slug,
            "version": {
                "name": "main",
                "type": BRANCH,
                "commit": "a" * 40,
            },
        }

    def _mock_storage(self, storages_mock):
        storage_mock = storages_mock.__getitem__.return_value
        storage_mock.generate_presigned_post.return_value = {
            "url": "https://storage.example.com/build-uploads",
            "fields": {"key": "1/1/artifacts.zip"},
        }
        return storage_mock

    def test_requires_authentication(self):
        self.client.credentials()
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_payload(self):
        response = self.client.post(self.url, {"project": self.project.slug}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_project_not_found(self):
        self.data["project"] = "does-not-exist"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_without_admin_permission(self):
        other_project = fixture.get(
            Project,
            slug="other-project",
            related_projects=[],
            main_language_project=None,
            users=[self.other_user],
            versions=[],
        )
        self.feature.projects.add(other_project)
        self.data["project"] = other_project.slug
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_feature_not_enabled(self):
        self.project.feature_set.all().delete()
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_not_active(self):
        self.project.skip = True
        self.project.save()
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(RTD_UPLOAD_API_MAX_PENDING_UPLOADS=1)
    @mock.patch("readthedocs.upload.api.views.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_too_many_pending_uploads(self, storages_mock, send_build_status):
        self._mock_storage(storages_mock)
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @mock.patch("readthedocs.upload.api.views.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_creates_build_and_version(self, storages_mock, send_build_status):
        storage_mock = self._mock_storage(storages_mock)
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        build = Build.objects.get(pk=response.data["build"]["id"])
        self.assertEqual(build.project, self.project)
        self.assertEqual(build.commit, "a" * 40)
        self.assertEqual(build.state, BUILD_STATE_TRIGGERED)
        self.assertTrue(build.is_uploaded)

        version = self.project.versions.get(verbose_name="main", type=BRANCH)
        self.assertEqual(version.identifier, "main")
        self.assertEqual(version.privacy_level, PUBLIC)
        self.assertTrue(version.active)

        self.assertEqual(response.data["upload_url"]["url"], storage_mock.generate_presigned_post.return_value["url"])
        storage_mock.generate_presigned_post.assert_called_once_with(
            key=build.uploaded_artifacts_storage_path,
            expires_in=mock.ANY,
            content_type="application/zip",
            max_size=mock.ANY,
        )
        send_build_status.delay.assert_called_once_with(
            build_pk=build.id,
            commit="a" * 40,
            status=mock.ANY,
        )

    @mock.patch("readthedocs.upload.api.views.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_reuses_existing_version(self, storages_mock, send_build_status):
        self._mock_storage(storages_mock)
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            type=BRANCH,
            privacy_level=PRIVATE,
        )

        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.project.versions.filter(verbose_name="main", type=BRANCH).count(), 1)

        version.refresh_from_db()
        self.assertEqual(version.privacy_level, PUBLIC)
        self.assertEqual(response.data["version"]["id"], version.pk)

    @mock.patch("readthedocs.upload.api.views.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_external_version_type(self, storages_mock, send_build_status):
        self._mock_storage(storages_mock)
        self.data["version"] = {
            "name": "123",
            "type": EXTERNAL,
            "commit": "b" * 40,
        }
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        version = self.project.versions.get(verbose_name="123", type=EXTERNAL)
        self.assertEqual(version.identifier, "123")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    @mock.patch("readthedocs.upload.api.views.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_private_version_allowed(self, storages_mock, send_build_status):
        self._mock_storage(storages_mock)
        self.data["version"]["privacy_level"] = PRIVATE
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        version = self.project.versions.get(verbose_name="main", type=BRANCH)
        self.assertEqual(version.privacy_level, PRIVATE)

    def test_private_version_not_allowed(self):
        self.data["version"]["privacy_level"] = PRIVATE
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch("readthedocs.core.utils.app")
    @mock.patch("readthedocs.upload.api.views.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_cancels_running_builds_for_same_version(self, storages_mock, send_build_status, app_mock):
        self._mock_storage(storages_mock)
        version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            type=BRANCH,
        )
        running_build = fixture.get(
            Build,
            project=self.project,
            version=version,
            state=BUILD_STATE_BUILDING,
            task_id="task-1",
        )

        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        app_mock.control.revoke.assert_called_once_with(
            "task-1",
            signal="SIGINT",
            terminate=True,
        )
        self.assertNotEqual(running_build.pk, response.data["build"]["id"])

    @override_settings(RTD_DOCKER_COMPOSE=True, USING_AWS=False)
    @mock.patch("readthedocs.upload.api.views.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_docker_compose_replaces_storage_hostname(self, storages_mock, send_build_status):
        storage_mock = self._mock_storage(storages_mock)
        storage_mock.generate_presigned_post.return_value = {
            "url": "http://storage/build-uploads",
            "fields": {"key": "1/1/artifacts.zip"},
        }
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["upload_url"]["url"], "http://127.0.0.1/build-uploads")


class UploadCompleteViewTests(UploadAPIEndpointMixin):
    def setUp(self):
        super().setUp()
        self.url = reverse("upload-api-complete")
        self.version = fixture.get(
            Version,
            project=self.project,
            verbose_name="main",
            type=BRANCH,
        )
        self.build = fixture.get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_TRIGGERED,
            is_uploaded=True,
            task_id=None,
        )
        self.data = {"build": self.build.pk, "status": UploadStatus.success.value}

    def test_requires_authentication(self):
        self.client.credentials()
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_payload(self):
        response = self.client.post(self.url, {"build": self.build.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_build_not_found(self):
        self.data["build"] = self.build.pk + 1000
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_build_not_uploaded_is_not_found(self):
        self.build.is_uploaded = False
        self.build.save()
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_without_admin_permission(self):
        other_project = fixture.get(
            Project,
            slug="other-project",
            related_projects=[],
            main_language_project=None,
            users=[self.other_user],
            versions=[],
        )
        other_version = fixture.get(Version, project=other_project)
        other_build = fixture.get(
            Build,
            project=other_project,
            version=other_version,
            state=BUILD_STATE_TRIGGERED,
            is_uploaded=True,
            task_id=None,
        )
        self.data["build"] = other_build.pk
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_build_already_has_task_id(self):
        self.build.task_id = "already-queued"
        self.build.save()
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_build_not_in_triggered_state(self):
        self.build.state = BUILD_STATE_FINISHED
        self.build.save()
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_upload_failed(self):
        self.data["status"] = UploadStatus.failed.value
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.build.refresh_from_db()
        self.assertEqual(self.build.state, BUILD_STATE_FINISHED)
        self.assertFalse(self.build.success)

        notification = Notification.objects.get(
            attached_to_content_type__model="build",
            attached_to_id=self.build.pk,
        )
        self.assertEqual(notification.message_id, BuildUserError.BUILD_ARTIFACTS_ZIP_UPLOAD_FAILED)

    @mock.patch("readthedocs.upload.api.views.storages")
    def test_success_missing_artifacts_in_storage(self, storages_mock):
        storage_mock = storages_mock.__getitem__.return_value
        storage_mock.exists.return_value = False

        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        storage_mock.exists.assert_called_once_with(self.build.uploaded_artifacts_storage_path)

    @mock.patch("readthedocs.upload.api.views.process_uploaded_build")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_success_triggers_processing_task(self, storages_mock, process_uploaded_build):
        storage_mock = storages_mock.__getitem__.return_value
        storage_mock.exists.return_value = True
        process_uploaded_build.apply_async.return_value = mock.Mock(id="task-id-123")

        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        self.build.refresh_from_db()
        self.assertEqual(self.build.task_id, "task-id-123")

        process_uploaded_build.apply_async.assert_called_once()
        call_kwargs = process_uploaded_build.apply_async.call_args.kwargs
        self.assertEqual(call_kwargs["kwargs"]["build_id"], self.build.id)
        self.assertNotIn("countdown", call_kwargs)

    @mock.patch("readthedocs.upload.api.views.process_uploaded_build")
    @mock.patch("readthedocs.upload.api.views.storages")
    @mock.patch.object(Build.objects, "concurrent")
    def test_success_delayed_when_concurrency_limit_reached(
        self, concurrent_mock, storages_mock, process_uploaded_build
    ):
        concurrent_mock.return_value = (True, 5, 4)
        storage_mock = storages_mock.__getitem__.return_value
        storage_mock.exists.return_value = True
        process_uploaded_build.apply_async.return_value = mock.Mock(id="task-id-456")

        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        call_kwargs = process_uploaded_build.apply_async.call_args.kwargs
        self.assertIn("countdown", call_kwargs)

        notification = Notification.objects.get(
            attached_to_content_type__model="build",
            attached_to_id=self.build.pk,
        )
        self.assertEqual(notification.message_id, BuildMaxConcurrencyError.LIMIT_REACHED)
