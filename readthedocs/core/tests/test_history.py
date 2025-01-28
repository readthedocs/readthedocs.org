from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.projects.models import Project


class TestHistoricalModels(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.client.force_login(self.user)

    @mock.patch("readthedocs.projects.forms.trigger_build", mock.MagicMock())
    def test_extra_historical_fields_with_request(self):
        self.assertEqual(self.project.history.count(), 1)
        r = self.client.post(
            reverse("projects_edit", args=[self.project.slug]),
            data={
                "name": "Changed!",
                "repo": "https://github.com/readthedocs/readthedocs",
                "repo_type": self.project.repo_type,
                "default_version": self.project.default_version,
                "language": self.project.language,
                "versioning_scheme": self.project.versioning_scheme,
            },
            headers={"user-agent": "Firefox"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.project.history.count(), 2)
        history = self.project.history.first()
        self.assertEqual(history.name, "Changed!")
        self.assertEqual(history.history_user, self.user)
        self.assertEqual(history.extra_history_user_id, self.user.id)
        self.assertEqual(history.extra_history_user_username, self.user.username)
        self.assertEqual(history.extra_history_ip, "127.0.0.1")
        self.assertEqual(history.extra_history_browser, "Firefox")

    def test_extra_historical_fields_outside_request(self):
        self.assertEqual(self.project.history.count(), 1)
        self.project.name = "Changed!"
        self.project.save()
        self.assertEqual(self.project.history.count(), 2)
        history = self.project.history.first()
        self.assertEqual(history.name, "Changed!")
        self.assertIsNone(history.history_user)
        self.assertIsNone(history.extra_history_user_id)
        self.assertIsNone(history.extra_history_user_username)
        self.assertIsNone(history.extra_history_ip)
        self.assertIsNone(history.extra_history_browser)
