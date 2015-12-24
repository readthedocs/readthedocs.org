from django.test import TestCase

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken

from readthedocs.projects.models import Project

from readthedocs.oauth.services import GitHubService
from readthedocs.oauth.models import RemoteRepository, RemoteOrganization


class RedirectOauth(TestCase):

    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug='pip')
        self.org = RemoteOrganization.objects.create(slug='rtfd', json='')
        self.privacy = self.project.version_privacy_level
        self.service = GitHubService(user=self.user, account=None)

    def test_make_github_project_pass(self):
        repo_json = {
            "name": "",
            "full_name": "",
            "description": "",
            "git_url": "",
            "private": False,
            "ssh_url": "",
            "html_url": "",
            "clone_url": "",
        }
        github_project = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy)
        self.assertIsInstance(github_project, RemoteRepository)

    def test_make_github_project_fail(self):
        repo_json = {
            "name": "",
            "full_name": "",
            "description": "",
            "git_url": "",
            "private": True,
            "ssh_url": "",
            "html_url": "",
            "clone_url": "",
        }
        github_project = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy)
        self.assertIsNone(github_project)

    def test_make_github_organization(self):
        org_json = {
            "html_url": "",
            "name": "",
            "email": "",
            "login": "",
        }
        org = self.service.create_organization(org_json)
        self.assertIsInstance(org, RemoteOrganization)

    def test_import_github_with_no_token(self):
        '''User without a GitHub SocialToken does not return a service'''
        service = GitHubService.for_user(self.user)
        self.assertIsNone(service)

    def test_multiple_users_same_repo(self):
        repo_json = {
            "name": "",
            "full_name": "testrepo/multiple",
            "description": "",
            "git_url": "",
            "private": False,
            "ssh_url": "",
            "html_url": "",
            "clone_url": "",
        }

        github_project = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy)

        user2 = User.objects.get(pk=2)
        service = GitHubService(user=user2, account=None)
        github_project_2 = service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy)
        self.assertIsInstance(github_project, RemoteRepository)
        self.assertIsInstance(github_project_2, RemoteRepository)
        self.assertNotEqual(github_project_2, github_project)

        github_project_3 = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy)
        github_project_4 = service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy)
        self.assertIsInstance(github_project_3, RemoteRepository)
        self.assertIsInstance(github_project_4, RemoteRepository)
        self.assertEqual(github_project, github_project_3)
        self.assertEqual(github_project_2, github_project_4)

        github_project_5 = self.service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy)
        github_project_6 = service.create_repository(
            repo_json, organization=self.org, privacy=self.privacy)

        self.assertEqual(github_project, github_project_5)
        self.assertEqual(github_project_2, github_project_6)
