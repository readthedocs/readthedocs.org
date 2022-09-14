from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project
from readthedocs.redirects.models import Redirect


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class TestViews(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, slug="test", users=[self.user])
        self.redirect = get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/404.html",
            to_url="/en/latest/",
        )
        self.client.force_login(self.user)

    def test_create_redirect(self):
        self.assertEqual(self.project.redirects.all().count(), 1)
        resp = self.client.post(
            reverse("projects_redirects_create", args=[self.project.slug]),
            data={
                "redirect_type": "page",
                "from_url": "/config.html",
                "to_url": "/configuration.html",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.project.redirects.all().count(), 2)

    def test_update_redirect(self):
        self.assertEqual(self.project.redirects.all().count(), 1)
        resp = self.client.post(
            reverse(
                "projects_redirects_edit", args=[self.project.slug, self.redirect.pk]
            ),
            data={
                "redirect_type": "page",
                "from_url": "/config.html",
                "to_url": "/configuration.html",
            },
        )
        self.assertEqual(resp.status_code, 302)
        redirect = self.project.redirects.get()
        self.assertEqual(redirect.redirect_type, "page")
        self.assertEqual(redirect.from_url, "/config.html")
        self.assertEqual(redirect.to_url, "/configuration.html")
        self.assertEqual(self.project.redirects.all().count(), 1)

    def test_delete_redirect(self):
        self.assertEqual(self.project.redirects.all().count(), 1)
        resp = self.client.post(
            reverse(
                "projects_redirects_delete", args=[self.project.slug, self.redirect.pk]
            ),
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.project.redirects.all().count(), 0)

    def test_list_redirect(self):
        resp = self.client.get(
            reverse("projects_redirects", args=[self.project.slug]),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.redirect.from_url)
        self.assertContains(resp, self.redirect.to_url)

    def test_get_redirect(self):
        resp = self.client.get(
            reverse(
                "projects_redirects_edit", args=[self.project.slug, self.redirect.pk]
            ),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.redirect.redirect_type)
        self.assertContains(resp, self.redirect.from_url)
        self.assertContains(resp, self.redirect.to_url)


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestViewsWithOrganizations(TestViews):
    def setUp(self):
        super().setUp()
        self.organization = get(
            Organization, projects=[self.project], owners=[self.user]
        )
