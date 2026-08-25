from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django_dynamic_fixture import get
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import EXTERNAL_VERSION_STATE_OPEN
from readthedocs.builds.constants import BUILD_STATUS_PENDING
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
from readthedocs.organizations.models import Organization
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project
from readthedocs.upload.api.serializers import UploadStatus


class UploadAPIEndpointMixin(TestCase):
    def setUp(self):
        self.user = get(
            User,
            username="testuser",
        )
        self.token = get(Token, key="me", user=self.user)

        self.project = get(
            Project,
            slug="project",
            users=[self.user],
        )
        self.organization = get(
            Organization,
            owners=[self.user],
            projects=[self.project],
        )
        self.feature = get(
            Feature,
            feature_id=Feature.ALLOW_DIRECT_ARTIFACTS_UPLOAD,
            projects=[self.project],
        )

        self.other_user = get(User, username="otheruser")

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
            "fields": {"key": "project/1/artifacts.zip"},
        }
        return storage_mock

    def test_requires_authentication(self):
        self.client.credentials()
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_payload(self):
        response = self.client.post(self.url, {"project": self.project.slug})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_project_not_found(self):
        self.data["project"] = "does-not-exist"
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_without_admin_permission(self):
        other_project = get(
            Project,
            slug="other-project",
            users=[self.other_user],
        )
        self.feature.projects.add(other_project)
        self.data["project"] = other_project.slug
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_feature_not_enabled(self):
        self.project.feature_set.all().delete()
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_project_not_active(self):
        self.project.skip = True
        self.project.save()
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(RTD_UPLOAD_API_MAX_PENDING_UPLOADS=2)
    @mock.patch("readthedocs.projects.tasks.utils.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_too_many_pending_uploads(self, storages_mock, send_build_status):
        self._mock_storage(storages_mock)
        self.data["version"]["name"] = "v1"
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_201_CREATED

        self.data["version"]["name"] = "v2"
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_201_CREATED

        self.data["version"]["name"] = "main"
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @mock.patch("readthedocs.projects.tasks.utils.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_creates_build_and_version(self, storages_mock, send_build_status):
        storage_mock = self._mock_storage(storages_mock)
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_201_CREATED

        build = Build.objects.get(pk=response.data["build"]["id"])
        assert build.project == self.project
        assert build.commit == "a" * 40
        assert build.state == BUILD_STATE_TRIGGERED
        assert build.is_uploaded

        version = self.project.versions.get(verbose_name="main", type=BRANCH)
        assert version.identifier == "main"
        assert version.privacy_level == PUBLIC
        assert version.active
        assert version.state == EXTERNAL_VERSION_STATE_OPEN

        assert (
            response.data["upload_url"]["url"]
            == storage_mock.generate_presigned_post.return_value["url"]
        )
        storage_mock.generate_presigned_post.assert_called_once_with(
            key=build.uploaded_artifacts_storage_path,
            expires_in=mock.ANY,
            content_type="application/zip",
            max_size=mock.ANY,
        )
        send_build_status.delay.assert_not_called()

    @mock.patch("readthedocs.projects.tasks.utils.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_reuses_existing_version(self, storages_mock, send_build_status):
        self._mock_storage(storages_mock)
        version = get(
            Version,
            project=self.project,
            verbose_name="main",
            identifier="foo",
            type=BRANCH,
            privacy_level=PRIVATE,
            active=False,
            state=None,
        )

        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert self.project.versions.filter(verbose_name="main", type=BRANCH).count() == 1

        version.refresh_from_db()
        assert response.data["version"]["id"] == version.pk
        assert version.identifier == "main"
        assert version.privacy_level == PUBLIC
        assert version.active
        assert version.state == EXTERNAL_VERSION_STATE_OPEN

    @mock.patch("readthedocs.projects.tasks.utils.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_external_version_type(self, storages_mock, send_build_status):
        storage_mock = self._mock_storage(storages_mock)
        self.data["version"] = {
            "name": "123",
            "type": EXTERNAL,
            "commit": "b" * 40,
        }
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_201_CREATED

        build = Build.objects.get(pk=response.data["build"]["id"])
        assert build.project == self.project
        assert build.commit == "b" * 40
        assert build.state == BUILD_STATE_TRIGGERED
        assert build.is_uploaded

        version = self.project.versions.get(verbose_name="123", type=EXTERNAL)
        assert version.identifier == "123"
        assert version.privacy_level == PUBLIC
        assert version.active

        assert (
            response.data["upload_url"]["url"]
            == storage_mock.generate_presigned_post.return_value["url"]
        )
        storage_mock.generate_presigned_post.assert_called_once_with(
            key=build.uploaded_artifacts_storage_path,
            expires_in=mock.ANY,
            content_type="application/zip",
            max_size=mock.ANY,
        )
        send_build_status.delay.assert_called_once_with(
            build.pk,
            "b" * 40,
            BUILD_STATUS_PENDING,
        )

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    @mock.patch("readthedocs.projects.tasks.utils.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_private_version_allowed(self, storages_mock, send_build_status):
        self._mock_storage(storages_mock)
        self.data["version"]["privacy_level"] = PRIVATE
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_201_CREATED
        version = self.project.versions.get(verbose_name="main", type=BRANCH)
        assert version.privacy_level == PRIVATE

    def test_private_version_not_allowed(self):
        self.data["version"]["privacy_level"] = PRIVATE
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @mock.patch("readthedocs.core.utils.app")
    @mock.patch("readthedocs.projects.tasks.utils.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_cancels_running_builds_for_same_version(self, storages_mock, send_build_status, app_mock):
        self._mock_storage(storages_mock)
        version = get(
            Version,
            project=self.project,
            verbose_name="main",
            type=BRANCH,
        )
        running_build = get(
            Build,
            project=self.project,
            version=version,
            state=BUILD_STATE_BUILDING,
            task_id="task-1",
        )

        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_201_CREATED

        app_mock.control.revoke.assert_called_once_with(
            "task-1",
            signal="SIGINT",
            terminate=True,
        )
        assert running_build.pk != response.data["build"]["id"]

    @override_settings(RTD_DOCKER_COMPOSE=True, USING_AWS=False)
    @mock.patch("readthedocs.projects.tasks.utils.send_build_status")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_docker_compose_replaces_storage_hostname(self, storages_mock, send_build_status):
        storage_mock = self._mock_storage(storages_mock)
        storage_mock.generate_presigned_post.return_value = {
            "url": "http://storage/build-uploads",
            "fields": {"key": "project/1/artifacts.zip"},
        }
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["upload_url"]["url"] == "http://127.0.0.1/build-uploads"


class UploadCompleteViewTests(UploadAPIEndpointMixin):
    def setUp(self):
        super().setUp()
        self.url = reverse("upload-api-complete")
        self.version = get(
            Version,
            project=self.project,
            verbose_name="main",
            type=BRANCH,
        )
        self.build = get(
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
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_payload(self):
        response = self.client.post(self.url, {"build": self.build.pk})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_build_not_found(self):
        self.data["build"] = self.build.pk + 1000
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_build_not_uploaded_is_not_found(self):
        self.build.is_uploaded = False
        self.build.save()
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_without_admin_permission(self):
        other_project = get(
            Project,
            slug="other-project",
            users=[self.other_user],
        )
        other_version = get(Version, project=other_project)
        other_build = get(
            Build,
            project=other_project,
            version=other_version,
            state=BUILD_STATE_TRIGGERED,
            is_uploaded=True,
            task_id=None,
        )
        self.data["build"] = other_build.pk
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_build_already_has_task_id(self):
        self.build.task_id = "already-queued"
        self.build.save()
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_build_not_in_triggered_state(self):
        self.build.state = BUILD_STATE_FINISHED
        self.build.save()
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_upload_failed(self):
        self.data["status"] = UploadStatus.failed.value
        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_200_OK

        self.build.refresh_from_db()
        assert self.build.state == BUILD_STATE_FINISHED
        assert not self.build.success

        notification = Notification.objects.get(
            attached_to_content_type__model="build",
            attached_to_id=self.build.pk,
        )
        assert notification.message_id == BuildUserError.BUILD_ARTIFACTS_ZIP_UPLOAD_FAILED

    @mock.patch("readthedocs.upload.api.views.storages")
    def test_success_missing_artifacts_in_storage(self, storages_mock):
        storage_mock = storages_mock.__getitem__.return_value
        storage_mock.exists.return_value = False

        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        storage_mock.exists.assert_called_once_with(self.build.uploaded_artifacts_storage_path)

    @mock.patch("readthedocs.core.utils.app")
    @mock.patch("readthedocs.upload.api.views.storages")
    def test_success_triggers_processing_task(self, storages_mock, app_mock):
        storage_mock = storages_mock.__getitem__.return_value
        storage_mock.exists.return_value = True
        app_mock.send_task.return_value = mock.Mock(id="task-id-123")

        response = self.client.post(self.url, self.data)
        assert response.status_code == status.HTTP_202_ACCEPTED

        self.build.refresh_from_db()
        assert self.build.task_id == "task-id-123"

        app_mock.send_task.assert_called_once()
        call_kwargs = app_mock.send_task.call_args.kwargs
        assert call_kwargs["kwargs"]["build_pk"] == self.build.id
