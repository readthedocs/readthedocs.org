from unittest import mock

import django_dynamic_fixture as fixture
from django import urls
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.core.models import UserProfile
from readthedocs.projects.admin import _extract_project_slug_from_url
from readthedocs.projects.models import Project


class ProjectAdminActionsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = fixture.get(User)
        cls.profile = fixture.get(UserProfile, user=cls.owner, banned=False)
        cls.admin = fixture.get(User, is_staff=True, is_superuser=True)
        cls.project = fixture.get(
            Project,
            main_language_project=None,
            users=[cls.owner],
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_project_ban_owner(self):
        self.assertFalse(self.owner.profile.banned)
        action_data = {
            ACTION_CHECKBOX_NAME: [self.project.pk],
            "action": "ban_owner",
            "index": 0,
        }
        resp = self.client.post(
            urls.reverse("admin:projects_project_changelist"),
            action_data,
        )
        self.assertTrue(self.project.users.filter(profile__banned=True).exists())
        self.assertFalse(self.project.users.filter(profile__banned=False).exists())

    def test_project_ban_multiple_owners(self):
        owner_b = fixture.get(User)
        profile_b = fixture.get(UserProfile, user=owner_b, banned=False)
        self.project.users.add(owner_b)
        self.assertFalse(self.owner.profile.banned)
        self.assertFalse(owner_b.profile.banned)
        action_data = {
            ACTION_CHECKBOX_NAME: [self.project.pk],
            "action": "ban_owner",
            "index": 0,
        }
        resp = self.client.post(
            urls.reverse("admin:projects_project_changelist"),
            action_data,
        )
        self.assertFalse(self.project.users.filter(profile__banned=True).exists())
        self.assertEqual(self.project.users.filter(profile__banned=False).count(), 2)

    def test_extract_project_slug_from_dashboard_url(self):
        assert (
            _extract_project_slug_from_url(
                "https://readthedocs.org/projects/pip/builds/12345/"
            )
            == "pip"
        )

    def test_extract_project_slug_from_subdomain_url(self):
        assert (
            _extract_project_slug_from_url("https://pip.readthedocs.io/en/latest/")
            == "pip"
        )

    def test_extract_project_slug_from_unknown_url_returns_none(self):
        assert _extract_project_slug_from_url("https://example.com/foo/bar") is None

    def test_spam_rule_checks_from_urls_view_get(self):
        resp = self.client.get(
            urls.reverse("admin:projects_project_spam_rule_checks_from_urls"),
        )
        assert resp.status_code == 200

    def test_spam_rule_checks_from_urls_view_post(self):
        urls_text = "\n".join(
            [
                f"https://{self.project.slug}.readthedocs.io/en/latest/",
                "https://no-such-project-slug.readthedocs.io/",
                "https://example.com/not/a/project",
            ]
        )
        resp = self.client.post(
            urls.reverse("admin:projects_project_spam_rule_checks_from_urls"),
            {"urls": urls_text},
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert self.project.slug in content
        assert "no-such-project-slug" in content
        assert "example.com" in content

    @mock.patch("readthedocs.projects.admin.clean_project_resources")
    def test_project_delete(self, clean_project_resources):
        """Test project and artifacts are removed."""
        action_data = {
            ACTION_CHECKBOX_NAME: [self.project.pk],
            "action": "delete_selected",
            "index": 0,
            "post": "yes",
        }
        resp = self.client.post(
            urls.reverse("admin:projects_project_changelist"),
            action_data,
        )
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        clean_project_resources.assert_has_calls(
            [
                mock.call(
                    self.project,
                ),
            ]
        )
