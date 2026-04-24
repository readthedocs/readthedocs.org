import django_dynamic_fixture as fixture
from corsheaders.middleware import (
    ACCESS_CONTROL_ALLOW_CREDENTIALS,
    ACCESS_CONTROL_ALLOW_METHODS,
    ACCESS_CONTROL_ALLOW_ORIGIN,
)
from django.test import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.organizations.models import Organization
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import Domain, HTTPHeader

from .base import BaseDocServing


@override_settings(
    PUBLIC_DOMAIN="dev.readthedocs.io",
    PUBLIC_DOMAIN_USES_HTTPS=True,
    RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
)
class ProxitoHeaderTests(BaseDocServing):
    def test_redirect_headers(self):
        r = self.client.get(
            "", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["X-RTD-Redirect"], "system")
        self.assertEqual(
            r["Location"],
            "https://project.dev.readthedocs.io/en/latest/",
        )
        self.assertEqual(r["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Project"], "project")
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")
        self.assertEqual(r["X-RTD-Domain"], "project.dev.readthedocs.io")
        self.assertIsNone(r.get("X-RTD-Version"))
        self.assertIsNone(r.get("X-RTD-Path"))

    def test_serve_headers(self):
        r = self.client.get(
            "/en/latest/", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Tag"], "project,project:latest")
        self.assertEqual(r["X-RTD-Domain"], "project.dev.readthedocs.io")
        self.assertEqual(r["X-RTD-Project"], "project")
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")
        self.assertEqual(r["X-RTD-Version"], "latest")
        self.assertEqual(r["X-RTD-version-Method"], "path")
        self.assertEqual(r["X-RTD-Resolver-Filename"], "/")
        self.assertEqual(
            r["X-RTD-Path"], "/proxito/media/html/project/latest/index.html"
        )

    def test_serve_headers_with_path(self):
        r = self.client.get(
            "/en/latest/guides/jupyter/gallery.html",
            secure=True,
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Tag"], "project,project:latest")
        self.assertEqual(r["X-RTD-Domain"], "project.dev.readthedocs.io")
        self.assertEqual(r["X-RTD-Project"], "project")
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")
        self.assertEqual(r["X-RTD-Version"], "latest")
        self.assertEqual(r["X-RTD-version-Method"], "path")
        self.assertEqual(r["X-RTD-Resolver-Filename"], "/guides/jupyter/gallery.html")
        self.assertEqual(
            r["X-RTD-Path"],
            "/proxito/media/html/project/latest/guides/jupyter/gallery.html",
        )

    # refs https://read-the-docs.sentry.io/issues/5019718893/
    def test_serve_headers_with_unicode(self):
        r = self.client.get(
            "/en/latest/tutorial_1installation.htmlReview%20of%20Failures%20of%0BReview%20of%20Failures%20of%0BPhotovoltaic%20Moduleshotovoltaic%20Modules",
            secure=True,
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Tag"], "project,project:latest")
        self.assertEqual(r["X-RTD-Domain"], "project.dev.readthedocs.io")
        self.assertEqual(r["X-RTD-Project"], "project")
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")
        self.assertEqual(r["X-RTD-Version"], "latest")
        self.assertEqual(r["X-RTD-version-Method"], "path")
        self.assertEqual(
            r["X-RTD-Resolver-Filename"],
            "/tutorial_1installation.htmlReview%20of%20Failures%20of%0BReview%20of%20Failures%20of%0BPhotovoltaic%20Moduleshotovoltaic%20Modules",
        )
        self.assertEqual(
            r["X-RTD-Path"],
            "/proxito/media/html/project/latest/tutorial_1installation.htmlReview%20of%20Failures%20of%0BReview%20of%20Failures%20of%0BPhotovoltaic%20Moduleshotovoltaic%20Modules",
        )

    def test_subproject_serve_headers(self):
        r = self.client.get(
            "/projects/subproject/en/latest/",
            secure=True,
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Tag"], "subproject,subproject:latest")
        self.assertEqual(r["X-RTD-Domain"], "project.dev.readthedocs.io")
        self.assertEqual(r["X-RTD-Project"], "subproject")

        # I think it's not accurate saying that it's `subdomain` the method
        # that we use to get the project slug here, since it was in fact the
        # URL's path but we don't have that feature built
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")

        self.assertEqual(r["X-RTD-Version"], "latest")
        self.assertEqual(r["X-RTD-version-Method"], "path")
        self.assertEqual(
            r["X-RTD-Path"], "/proxito/media/html/subproject/latest/index.html"
        )

    def test_404_headers(self):
        r = self.client.get(
            "/foo/bar.html", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Domain"], "project.dev.readthedocs.io")
        self.assertEqual(r["X-RTD-Project"], "project")
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")
        self.assertEqual(r["X-RTD-version-Method"], "path")
        self.assertIsNone(r.get("X-RTD-Version"))
        self.assertIsNone(r.get("X-RTD-Path"))

    def test_custom_domain_headers(self):
        hostname = "docs.random.com"
        self.domain = fixture.get(
            Domain,
            project=self.project,
            domain=hostname,
            https=False,
        )
        r = self.client.get("/en/latest/", headers={"host": hostname})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Tag"], "project,project:latest")
        self.assertEqual(r["X-RTD-Domain"], self.domain.domain)
        self.assertEqual(r["X-RTD-Project"], self.project.slug)
        self.assertEqual(r["X-RTD-Project-Method"], "custom_domain")
        self.assertEqual(r["X-RTD-Version"], "latest")
        self.assertEqual(r["X-RTD-version-Method"], "path")
        self.assertEqual(
            r["X-RTD-Path"], "/proxito/media/html/project/latest/index.html"
        )

    def test_user_domain_headers(self):
        hostname = "docs.domain.com"
        self.domain = fixture.get(
            Domain,
            project=self.project,
            domain=hostname,
            https=False,
        )
        http_header = "X-My-Header"
        http_header_secure = "X-My-Secure-Header"
        http_header_value = "Header Value; Another Value;"
        fixture.get(
            HTTPHeader,
            domain=self.domain,
            name=http_header,
            value=http_header_value,
            only_if_secure_request=False,
        )
        fixture.get(
            HTTPHeader,
            domain=self.domain,
            name=http_header_secure,
            value=http_header_value,
            only_if_secure_request=True,
        )

        r = self.client.get("/en/latest/", headers={"host": hostname})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[http_header], http_header_value)
        self.assertFalse(r.has_header(http_header_secure))

        r = self.client.get("/en/latest/", headers={"host": hostname}, secure=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[http_header], http_header_value)
        self.assertEqual(r[http_header_secure], http_header_value)

    def test_force_addons_header(self):
        r = self.client.get(
            "/en/latest/", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.get("X-RTD-Force-Addons"))
        self.assertEqual(r["X-RTD-Force-Addons"], "true")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cors_headers_external_version(self):
        get(
            Version,
            project=self.project,
            slug="111",
            active=True,
            privacy_level=PUBLIC,
            type=EXTERNAL,
        )

        # Normal request
        r = self.client.get(
            "/en/111/",
            secure=True,
            headers={"host": "project--111.dev.readthedocs.build"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_ORIGIN], "*")
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, r.headers)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_METHODS], "HEAD, OPTIONS, GET")

        # Cross-origin request
        r = self.client.get(
            "/en/111/",
            secure=True,
            headers={
                "host": "project--111.dev.readthedocs.build",
                "origin": "https://example.com",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_ORIGIN], "*")
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, r.headers)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_METHODS], "HEAD, OPTIONS, GET")

    @override_settings(ALLOW_PRIVATE_REPOS=True, RTD_ALLOW_ORGANIZATIONS=True)
    def test_cors_headers_private_version(self):
        get(Organization, owners=[self.eric], projects=[self.project])
        self.version.privacy_level = PRIVATE
        self.version.save()

        self.client.force_login(self.eric)

        # Normal request
        r = self.client.get(
            "/en/latest/",
            secure=True,
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_ORIGIN], "*")
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, r.headers)

        # Cross-origin request
        r = self.client.get(
            "/en/latest/",
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
                "origin": "https://example.com",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_ORIGIN], "*")
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, r.headers)

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cors_headers_public_version(self):
        # Normal request
        r = self.client.get(
            "/en/latest/",
            secure=True,
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_ORIGIN], "*")
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, r.headers)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_METHODS], "HEAD, OPTIONS, GET")

        # Cross-origin request
        r = self.client.get(
            "/en/latest/",
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
                "origin": "https://example.com",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_ORIGIN], "*")
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, r.headers)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_METHODS], "HEAD, OPTIONS, GET")

    @override_settings(ALLOW_PRIVATE_REPOS=True, RTD_ALLOW_ORGANIZATIONS=True)
    def test_cors_headers_public_version_with_organizations(self):
        get(Organization, owners=[self.eric], projects=[self.project])

        self.client.force_login(self.eric)

        # Normal request
        r = self.client.get(
            "/en/latest/",
            secure=True,
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_ORIGIN], "*")
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, r.headers)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_METHODS], "HEAD, OPTIONS, GET")

        # Cross-origin request
        r = self.client.get(
            "/en/latest/",
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
                "origin": "https://example.com",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_ORIGIN], "*")
        self.assertNotIn(ACCESS_CONTROL_ALLOW_CREDENTIALS, r.headers)
        self.assertEqual(r[ACCESS_CONTROL_ALLOW_METHODS], "HEAD, OPTIONS, GET")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cache_headers_public_version_with_private_projects_not_allowed(self):
        r = self.client.get(
            "/en/latest/", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_cache_headers_public_version_with_private_projects_allowed(self):
        r = self.client.get(
            "/en/latest/", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cache_headers_robots_txt_with_private_projects_not_allowed(self):
        r = self.client.get(
            "/robots.txt", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")
        self.assertEqual(r["Cache-Tag"], "project,project:robots.txt")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_cache_headers_robots_txt_with_private_projects_allowed(self):
        r = self.client.get(
            "/robots.txt", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")
        self.assertEqual(r["Cache-Tag"], "project,project:robots.txt")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cache_headers_robots_txt_with_private_projects_not_allowed(self):
        r = self.client.get(
            "/sitemap.xml", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")
        self.assertEqual(r["Cache-Tag"], "project,project:sitemap.xml")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_cache_headers_robots_txt_with_private_projects_allowed(self):
        r = self.client.get(
            "/sitemap.xml", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")
        self.assertEqual(r["Cache-Tag"], "project,project:sitemap.xml")

    def test_cache_headers_at_browser_level_on_external_domain(self):
        r = self.client.get(
            "/en/latest/", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("no-cache", r.headers)

        get(
            Version,
            project=self.project,
            slug="111",
            active=True,
            privacy_level=PUBLIC,
            type=EXTERNAL,
        )

        r = self.client.get(
            "/en/111/",
            secure=True,
            headers={"host": "project--111.dev.readthedocs.build"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Control"], "no-cache")

    def test_x_robots_tag_header(self):
        r = self.client.get(
            "/en/latest/", secure=True, headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("X-Robots-Tag", r.headers)

        get(
            Version,
            project=self.project,
            slug="111",
            active=True,
            privacy_level=PUBLIC,
            type=EXTERNAL,
        )

        r = self.client.get(
            "/en/111/",
            secure=True,
            headers={"host": "project--111.dev.readthedocs.build"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["X-Robots-Tag"], "noindex")
