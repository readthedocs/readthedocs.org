from django.test import TestCase

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken

from readthedocs.projects.models import Project

from readthedocs.oauth.utils import import_github
from readthedocs.oauth.models import OAuthRepository, OAuthOrganization


class RedirectOauth(TestCase):

    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug='pip')
        self.org = OAuthOrganization.objects.create(slug='rtfd', json='')
        self.privacy = self.project.version_privacy_level

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
        github_project = OAuthRepository.objects.create_from_github_api(
            repo_json, user=self.user, organization=self.org,
            privacy=self.privacy)
        self.assertIsInstance(github_project, OAuthRepository)

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
        github_project = OAuthRepository.objects.create_from_github_api(
            repo_json, user=self.user, organization=self.org,
            privacy=self.privacy)
        self.assertIsNone(github_project)

    def test_make_github_organization(self):
        org_json = {
            "html_url": "",
            "name": "",
            "email": "",
            "login": "",
        }
        org = OAuthOrganization.objects.create_from_github_api(
            org_json, user=self.user)
        self.assertIsInstance(org, OAuthOrganization)

    def test_import_github_with_no_token(self):
        github_connected = import_github(self.user, sync=True)
        self.assertEqual(github_connected, False)

    def test_multiple_users_same_repo(self):
        user2 = User.objects.get(pk=2)
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

        github_project = OAuthRepository.objects.create_from_github_api(
            repo_json, user=self.user, organization=self.org,
            privacy=self.privacy)
        github_project_2 = OAuthRepository.objects.create_from_github_api(
            repo_json, user=user2, organization=self.org, privacy=self.privacy)
        self.assertIsInstance(github_project, OAuthRepository)
        self.assertIsInstance(github_project_2, OAuthRepository)
        self.assertNotEqual(github_project_2, github_project)

        github_project_3 = OAuthRepository.objects.create_from_github_api(
            repo_json, user=self.user, organization=self.org,
            privacy=self.privacy)
        github_project_4 = OAuthRepository.objects.create_from_github_api(
            repo_json, user=user2, organization=self.org, privacy=self.privacy)
        self.assertIsInstance(github_project_3, OAuthRepository)
        self.assertIsInstance(github_project_4, OAuthRepository)
        self.assertEqual(github_project, github_project_3)
        self.assertEqual(github_project_2, github_project_4)

        github_project_5 = OAuthRepository.objects.create_from_github_api(
            repo_json, user=self.user, organization=self.org,
            privacy=self.privacy)
        github_project_6 = OAuthRepository.objects.create_from_github_api(
            repo_json, user=user2, organization=self.org, privacy=self.privacy)

        self.assertEqual(github_project, github_project_5)
        self.assertEqual(github_project_2, github_project_6)
