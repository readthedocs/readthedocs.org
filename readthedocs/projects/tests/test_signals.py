from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get
from readthedocs.integrations.models import Integration
from readthedocs.oauth.constants import GITHUB, GITHUB_APP
from readthedocs.oauth.models import GitHubAppInstallation, RemoteRepository
from readthedocs.projects.models import Project


class TestProjectSignals(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])

    def test_create_github_app_integration(self):
        github_repo = get(
            RemoteRepository,
            vcs_provider=GITHUB,
        )
        github_app_repo = get(
            RemoteRepository,
            vcs_provider=GITHUB_APP,
            github_app_installation=get(GitHubAppInstallation)
        )

        assert not self.project.is_github_app_project
        assert not self.project.integrations.exists()

        # Not a GitHub App repository, no integration created.
        self.project.remote_repository = github_repo
        self.project.save()
        assert not self.project.is_github_app_project
        assert not self.project.integrations.exists()

        # Now set the remote repository to a GitHub App repository.
        self.project.remote_repository = github_app_repo
        self.project.save()
        assert self.project.is_github_app_project
        integration = self.project.integrations.first()
        assert integration.integration_type == Integration.GITHUBAPP

        # Even if the connection is removed, the integration should still exist.
        self.project.remote_repository = None
        self.project.save()
        assert not self.project.is_github_app_project
        integration = self.project.integrations.first()
        assert integration.integration_type == Integration.GITHUBAPP
