from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project
from readthedocs.redirects.constants import (
    CLEAN_URL_TO_HTML_REDIRECT,
    EXACT_REDIRECT,
    HTML_TO_CLEAN_URL_REDIRECT,
    PAGE_REDIRECT,
)
from readthedocs.redirects.models import Redirect
from readthedocs.subscriptions.constants import TYPE_REDIRECTS_LIMIT
from readthedocs.subscriptions.products import RTDProductFeature


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class TestViews(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, slug="test", users=[self.user])
        self.redirect = get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/404.html",
            to_url="/en/latest/",
        )
        self.client.force_login(self.user)

    def test_create_redirect(self):
        self.assertEqual(self.project.redirects.all().count(), 1)
        resp = self.client.post(
            reverse("projects_redirects_create", args=[self.project.slug]),
            data={
                "redirect_type": PAGE_REDIRECT,
                "from_url": "/config.html",
                "to_url": "/configuration.html",
                "http_status": 302,
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
                "redirect_type": PAGE_REDIRECT,
                "from_url": "/config.html",
                "to_url": "/configuration.html",
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 302)
        redirect = self.project.redirects.get()
        self.assertEqual(redirect.redirect_type, PAGE_REDIRECT)
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

    def test_redirects_position(self):
        self.project.redirects.all().delete()
        for msg in ["one", "two", "three"]:
            resp = self.client.post(
                reverse("projects_redirects_create", args=[self.project.slug]),
                data={
                    "redirect_type": EXACT_REDIRECT,
                    "from_url": "/config.html",
                    "to_url": "/configuration.html",
                    "http_status": 302,
                    "description": msg,
                },
            )
            self.assertEqual(resp.status_code, 302)

        self.assertEqual(self.project.redirects.all().count(), 3)

        redirect_one = self.project.redirects.get(description="one")
        redirect_two = self.project.redirects.get(description="two")
        redirect_three = self.project.redirects.get(description="three")

        self.assertEqual(redirect_three.position, 0)
        self.assertEqual(redirect_two.position, 1)
        self.assertEqual(redirect_one.position, 2)

        # Move to the top
        resp = self.client.post(
            reverse(
                "projects_redirects_insert",
                args=[self.project.slug, redirect_one.pk, 0],
            ),
        )
        self.assertEqual(resp.status_code, 302)

        # Move down
        resp = self.client.post(
            reverse(
                "projects_redirects_insert",
                args=[self.project.slug, redirect_three.pk, 2],
            ),
        )
        self.assertEqual(resp.status_code, 302)

        redirect_one.refresh_from_db()
        redirect_two.refresh_from_db()
        redirect_three.refresh_from_db()
        self.assertEqual(redirect_one.position, 0)
        self.assertEqual(redirect_two.position, 1)
        self.assertEqual(redirect_three.position, 2)

        resp = self.client.post(
            reverse(
                "projects_redirects_delete", args=[self.project.slug, redirect_one.pk]
            ),
        )
        self.assertEqual(resp.status_code, 302)

        redirect_two.refresh_from_db()
        redirect_three.refresh_from_db()
        self.assertEqual(redirect_two.position, 0)
        self.assertEqual(redirect_three.position, 1)

    def test_redirects_validations(self):
        url = reverse("projects_redirects_create", args=[self.project.slug])
        resp = self.client.post(
            url,
            data={
                "redirect_type": EXACT_REDIRECT,
                "from_url": "/one/$rest",
                "to_url": "/two/",
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "The $rest wildcard has been removed in favor of *.")

        resp = self.client.post(
            url,
            data={
                "redirect_type": EXACT_REDIRECT,
                "from_url": "/one/*.html",
                "to_url": "/two/",
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "The * wildcard must be at the end of the path.")

        resp = self.client.post(
            url,
            data={
                "redirect_type": EXACT_REDIRECT,
                "from_url": "/one/",
                "to_url": "/two/:splat",
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(
            resp,
            "The * wildcard must be at the end of from_url to use the :splat placeholder in to_url.",
        )

        get(Redirect, redirect_type=CLEAN_URL_TO_HTML_REDIRECT, project=self.project)
        resp = self.client.post(
            url,
            data={
                "redirect_type": CLEAN_URL_TO_HTML_REDIRECT,
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(
            resp,
            "Only one redirect of type `clean_url_to_html` is allowed per project.",
        )

        get(Redirect, redirect_type=HTML_TO_CLEAN_URL_REDIRECT, project=self.project)
        resp = self.client.post(
            url,
            data={
                "redirect_type": HTML_TO_CLEAN_URL_REDIRECT,
                "from_url": "/one/",
                "to_url": "/two/",
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(
            resp,
            "Only one redirect of type `html_to_clean_url` is allowed per project.",
        )

    @override_settings(
        RTD_DEFAULT_FEATURES=dict(
            (
                RTDProductFeature(
                    type=TYPE_REDIRECTS_LIMIT,
                    value=2,
                ).to_item(),
            )
        )
    )
    def test_redirects_limit(self):
        self.assertEqual(self.project.redirects.all().count(), 1)
        url = reverse("projects_redirects_create", args=[self.project.slug])
        resp = self.client.post(
            url,
            data={
                "redirect_type": EXACT_REDIRECT,
                "from_url": "a",
                "to_url": "b",
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(
            url,
            data={
                "redirect_type": EXACT_REDIRECT,
                "from_url": "c",
                "to_url": "d",
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(
            resp,
            "This project has reached the limit of 2 redirects.",
        )
        self.assertEqual(self.project.redirects.all().count(), 2)

        # Update works
        resp = self.client.post(
            reverse(
                "projects_redirects_edit", args=[self.project.slug, self.redirect.pk]
            ),
            data={
                "redirect_type": PAGE_REDIRECT,
                "http_status": 302,
            },
        )
        self.assertEqual(resp.status_code, 302)

        # Delete works
        resp = self.client.post(
            reverse(
                "projects_redirects_delete", args=[self.project.slug, self.redirect.pk]
            ),
        )
        self.assertEqual(resp.status_code, 302)


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestViewsWithOrganizations(TestViews):
    def setUp(self):
        super().setUp()
        self.organization = get(
            Organization, projects=[self.project], owners=[self.user]
        )
