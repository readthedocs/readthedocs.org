from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    BUILD_STATE_CANCELLED,
    BUILD_STATE_INSTALLING,
    BUILD_STATE_TRIGGERED,
)
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project


@mock.patch("readthedocs.builds.views.app")
class CancelBuildViewTests(TestCase):
    def setUp(self):
        self.user = get(User, username="test")
        self.project = get(Project, users=[self.user])
        self.version = get(Version, project=self.project)
        self.build = get(
            Build,
            project=self.project,
            version=self.version,
            task_id="1234",
            state=BUILD_STATE_INSTALLING,
        )

    def test_cancel_running_build(self, app):
        self.build.state = BUILD_STATE_INSTALLING
        self.build.save()
        self.client.force_login(self.user)
        url = reverse("builds_detail", args=[self.project.slug, self.build.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        app.control.revoke.assert_called_once_with(
            self.build.task_id, signal=mock.ANY, terminate=True
        )
        self.build.refresh_from_db()
        self.assertEqual(self.build.state, BUILD_STATE_INSTALLING)

    def test_cancel_triggered_build(self, app):
        self.build.state = BUILD_STATE_TRIGGERED
        self.build.save()
        self.client.force_login(self.user)
        url = reverse("builds_detail", args=[self.project.slug, self.build.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        app.control.revoke.assert_called_once_with(
            self.build.task_id, signal=mock.ANY, terminate=False
        )
        self.build.refresh_from_db()
        self.assertEqual(self.build.state, BUILD_STATE_CANCELLED)

    def test_cancel_build_anonymous_user(self, app):
        url = reverse("builds_detail", args=[self.project.slug, self.build.pk])
        self.client.logout()
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        app.control.revoke.assert_not_called()

    def test_cancel_build_from_another_project(self, app):
        another_user = get(User)
        another_project = get(Project, users=[another_user])
        another_build = get(
            Build, project=another_project, version=another_project.versions.first()
        )

        self.client.force_login(another_user)

        url = reverse("builds_detail", args=[self.project.slug, self.build.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)
        app.control.revoke.assert_not_called()

        url = reverse("builds_detail", args=[another_project.slug, self.build.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        app.control.revoke.assert_not_called()

        url = reverse("builds_detail", args=[another_project.slug, another_build.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        app.control.revoke.assert_called_once_with(
            another_build.task_id, signal=mock.ANY, terminate=True
        )
