from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.redirects.constants import (
    CLEAN_URL_TO_HTML_REDIRECT,
    EXACT_REDIRECT,
    HTML_TO_CLEAN_URL_REDIRECT,
)
from readthedocs.redirects.models import Redirect

from .mixins import APIEndpointMixin


class RedirectsEndpointTests(APIEndpointMixin):
    def test_unauthed_projects_redirects_list(self):
        response = self.client.get(
            reverse(
                "projects-redirects-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 401)

    def test_projects_redirects_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-redirects-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-redirects-list"),
        )

    def test_unauthed_projects_redirects_detail(self):
        response = self.client.get(
            reverse(
                "projects-redirects-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "redirect_pk": self.redirect.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 401)

    def test_projects_redirects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-redirects-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "redirect_pk": self.redirect.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-redirects-detail"),
        )

    def test_unauthed_projects_redirects_list_post(self):
        data = {}

        response = self.client.post(
            reverse(
                "projects-redirects-list",
                kwargs={
                    "parent_lookup_project__slug": self.others_project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            reverse(
                "projects-redirects-list",
                kwargs={
                    "parent_lookup_project__slug": self.others_project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 403)

    def test_projects_redirects_list_post(self):
        data = {
            "from_url": "/page/",
            "to_url": "/another/",
            "type": "page",
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            reverse(
                "projects-redirects-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        response_json["created"] = "2019-04-29T10:00:00Z"
        response_json["modified"] = "2019-04-29T12:00:00Z"
        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-redirects-list_POST"),
        )

    def test_projects_redirects_old_type_post(self):
        for redirect_type in ["prefix", "sphinx_html", "sphinx_htmldir"]:
            self.assertEqual(Redirect.objects.count(), 1)
            data = {
                "from_url": "/redirect-this/",
                "type": redirect_type,
            }

            self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
            response = self.client.post(
                reverse(
                    "projects-redirects-list",
                    kwargs={
                        "parent_lookup_project__slug": self.project.slug,
                    },
                ),
                data,
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(Redirect.objects.all().count(), 1)
            json_response = response.json()
            self.assertIn("type", json_response)

    def test_projects_redirects_type_clean_url_to_html_list_post(self):
        self.assertEqual(Redirect.objects.count(), 1)
        data = {
            "type": CLEAN_URL_TO_HTML_REDIRECT,
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            reverse(
                "projects-redirects-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Redirect.objects.all().count(), 2)

        redirect = Redirect.objects.first()
        self.assertEqual(redirect.redirect_type, CLEAN_URL_TO_HTML_REDIRECT)
        self.assertEqual(redirect.from_url, "")
        self.assertEqual(redirect.to_url, "")

    def test_projects_redirects_detail_put(self):
        url = reverse(
            "projects-redirects-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "redirect_pk": self.redirect.pk,
            },
        )
        data = {
            "from_url": "/changed/",
            "to_url": "/toanother/",
            "type": "page",
        }

        self.client.logout()
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        response_json["modified"] = "2019-04-29T12:00:00Z"
        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-redirects-detail_PUT"),
        )

    def test_projects_redirects_position(self):
        url = reverse(
            "projects-redirects-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # A new redirect will be created at the start by default.
        response = self.client.post(
            url,
            data={
                "from_url": "/one/",
                "to_url": "/two/",
                "type": EXACT_REDIRECT,
            },
        )
        self.assertEqual(response.status_code, 201)
        second_redirect = Redirect.objects.get(pk=response.json()["pk"])

        self.redirect.refresh_from_db()

        self.assertEqual(second_redirect.position, 0)
        self.assertEqual(self.redirect.position, 1)

        # Explicitly create a redirect at the end.
        response = self.client.post(
            url,
            data={
                "from_url": "/two/",
                "to_url": "/three/",
                "type": EXACT_REDIRECT,
                "position": 2,
            },
        )
        self.assertEqual(response.status_code, 201)
        third_redirect = Redirect.objects.get(pk=response.json()["pk"])

        self.redirect.refresh_from_db()
        second_redirect.refresh_from_db()

        self.assertEqual(second_redirect.position, 0)
        self.assertEqual(self.redirect.position, 1)
        self.assertEqual(third_redirect.position, 2)

        url = reverse(
            "projects-redirects-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "redirect_pk": self.redirect.pk,
            },
        )

        # Move redirect to the end.
        response = self.client.put(url, {"position": 2, "type": EXACT_REDIRECT})
        self.assertEqual(response.status_code, 200)

        self.redirect.refresh_from_db()
        second_redirect.refresh_from_db()
        third_redirect.refresh_from_db()

        self.assertEqual(second_redirect.position, 0)
        self.assertEqual(third_redirect.position, 1)
        self.assertEqual(self.redirect.position, 2)

        url = reverse(
            "projects-redirects-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "redirect_pk": second_redirect.pk,
            },
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        self.redirect.refresh_from_db()
        third_redirect.refresh_from_db()

        self.assertEqual(third_redirect.position, 0)
        self.assertEqual(self.redirect.position, 1)

    def test_projects_redirects_validations(self):
        url = reverse(
            "projects-redirects-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.post(
            url,
            data={
                "from_url": "/one/$rest",
                "to_url": "/two/",
                "type": EXACT_REDIRECT,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), ["The $rest wildcard has been removed in favor of *."]
        )

        response = self.client.post(
            url,
            data={
                "from_url": "/one/*.html",
                "to_url": "/two/",
                "type": EXACT_REDIRECT,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), ["The * wildcard must be at the end of the path."]
        )

        response = self.client.post(
            url,
            data={
                "from_url": "/one/",
                "to_url": "/two/:splat",
                "type": EXACT_REDIRECT,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            [
                "The * wildcard must be at the end of from_url to use the :splat placeholder in to_url."
            ],
        )

        get(Redirect, redirect_type=CLEAN_URL_TO_HTML_REDIRECT, project=self.project)
        response = self.client.post(
            url,
            data={
                "type": CLEAN_URL_TO_HTML_REDIRECT,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            ["Only one redirect of type `clean_url_to_html` is allowed per project."],
        )

        get(Redirect, redirect_type=HTML_TO_CLEAN_URL_REDIRECT, project=self.project)
        response = self.client.post(
            url,
            data={
                "type": HTML_TO_CLEAN_URL_REDIRECT,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            ["Only one redirect of type `html_to_clean_url` is allowed per project."],
        )

    def test_projects_redirects_detail_delete(self):
        url = reverse(
            "projects-redirects-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "redirect_pk": self.redirect.pk,
            },
        )

        self.client.logout()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

        self.assertEqual(self.project.redirects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.project.redirects.count(), 0)
