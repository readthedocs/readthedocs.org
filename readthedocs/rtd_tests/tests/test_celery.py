from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get
from messages_extends.models import Message

from readthedocs.builds import tasks as build_tasks
from readthedocs.builds.constants import BUILD_STATUS_SUCCESS, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.oauth.models import RemoteRepository, RemoteRepositoryRelation
from readthedocs.projects.models import Project


class TestCeleryBuilding(TestCase):

    """
    These tests run the build functions directly.

    They don't use celery
    """

    def setUp(self):
        super().setUp()
        self.eric = User(username="eric")
        self.eric.set_password("test")
        self.eric.save()
        self.project = Project.objects.create(
            name="Test Project",
        )
        self.project.users.add(self.eric)
        self.version = self.project.versions.get(slug=LATEST)

    @pytest.mark.skip
    def test_check_duplicate_no_reserved_version(self):
        create_git_branch(self.repo, "no-reserved")
        create_git_tag(self.repo, "no-reserved")

        version = self.project.versions.get(slug=LATEST)

        self.assertEqual(
            self.project.versions.filter(slug__startswith="no-reserved").count(), 0
        )

        sync_repository_task(version_id=version.pk)

        self.assertEqual(
            self.project.versions.filter(slug__startswith="no-reserved").count(), 2
        )

    def test_public_task_exception(self):
        """
        Test when a PublicTask rises an Exception.

        The exception should be caught and added to the ``info`` attribute of
        the result. Besides, the task should be SUCCESS.
        """
        from readthedocs.core.utils.tasks import PublicTask
        from readthedocs.worker import app

        @app.task(name="public_task_exception", base=PublicTask)
        def public_task_exception():
            raise Exception("Something bad happened")

        result = public_task_exception.delay()

        # although the task risen an exception, it's success since we add the
        # exception into the ``info`` attributes
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(
            result.info,
            {
                "task_name": "public_task_exception",
                "context": {},
                "public_data": {},
                "error": "Something bad happened",
            },
        )

    @patch("readthedocs.oauth.services.github.GitHubService.send_build_status")
    def test_send_build_status_with_remote_repo_github(self, send_build_status):
        self.project.repo = "https://github.com/test/test/"
        self.project.save()

        social_account = get(SocialAccount, user=self.eric, provider="gitlab")
        remote_repo = get(RemoteRepository)
        remote_repo.projects.add(self.project)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.eric,
            account=social_account,
        )

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(Build, project=self.project, version=external_version)
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_called_once_with(
            external_build,
            external_build.commit,
            BUILD_STATUS_SUCCESS,
        )
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 0)

    @patch("readthedocs.oauth.services.github.GitHubService.send_build_status")
    def test_send_build_status_with_social_account_github(self, send_build_status):
        social_account = get(SocialAccount, user=self.eric, provider="github")

        self.project.repo = "https://github.com/test/test/"
        self.project.save()

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(Build, project=self.project, version=external_version)
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_called_once_with(
            external_build,
            external_build.commit,
            BUILD_STATUS_SUCCESS,
        )
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 0)

    @patch("readthedocs.oauth.services.github.GitHubService.send_build_status")
    def test_send_build_status_no_remote_repo_or_social_account_github(
        self, send_build_status
    ):
        self.project.repo = "https://github.com/test/test/"
        self.project.save()
        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(Build, project=self.project, version=external_version)
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_not_called()
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 1)

    @patch("readthedocs.oauth.services.gitlab.GitLabService.send_build_status")
    def test_send_build_status_with_remote_repo_gitlab(self, send_build_status):
        self.project.repo = "https://gitlab.com/test/test/"
        self.project.save()

        social_account = get(SocialAccount, user=self.eric, provider="gitlab")
        remote_repo = get(RemoteRepository)
        remote_repo.projects.add(self.project)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.eric,
            account=social_account,
        )

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(Build, project=self.project, version=external_version)
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_called_once_with(
            external_build,
            external_build.commit,
            BUILD_STATUS_SUCCESS,
        )
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 0)

    @patch("readthedocs.oauth.services.gitlab.GitLabService.send_build_status")
    def test_send_build_status_with_social_account_gitlab(self, send_build_status):
        social_account = get(SocialAccount, user=self.eric, provider="gitlab")

        self.project.repo = "https://gitlab.com/test/test/"
        self.project.save()

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(Build, project=self.project, version=external_version)
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_called_once_with(
            external_build,
            external_build.commit,
            BUILD_STATUS_SUCCESS,
        )
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 0)

    @patch("readthedocs.oauth.services.gitlab.GitLabService.send_build_status")
    def test_send_build_status_no_remote_repo_or_social_account_gitlab(
        self, send_build_status
    ):
        self.project.repo = "https://gitlab.com/test/test/"
        self.project.save()
        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(Build, project=self.project, version=external_version)
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_not_called()
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 1)
