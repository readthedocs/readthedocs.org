import django_dynamic_fixture as fixture
from django.test import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Domain, Feature, HTTPHeader

from .base import BaseDocServing


@override_settings(
    PUBLIC_DOMAIN='dev.readthedocs.io',
    PUBLIC_DOMAIN_USES_HTTPS=True,
)
class ProxitoHeaderTests(BaseDocServing):

    def test_redirect_headers(self):
        r = self.client.get("", secure=True, HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['X-RTD-Redirect'], 'system')
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/',
        )
        self.assertEqual(r["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Project"], "project")
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")
        self.assertEqual(r["X-RTD-Domain"], "project.dev.readthedocs.io")
        self.assertIsNone(r.get("X-RTD-Version"))
        self.assertIsNone(r.get("X-RTD-Path"))

    def test_serve_headers(self):
        r = self.client.get(
            "/en/latest/", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Cache-Tag"], "project,project:latest")
        self.assertEqual(r["X-RTD-Domain"], "project.dev.readthedocs.io")
        self.assertEqual(r["X-RTD-Project"], "project")
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")
        self.assertEqual(r["X-RTD-Version"], "latest")
        self.assertEqual(r["X-RTD-version-Method"], "path")
        self.assertEqual(
            r["X-RTD-Path"], "/proxito/media/html/project/latest/index.html"
        )

    def test_subproject_serve_headers(self):
        r = self.client.get(
            "/projects/subproject/en/latest/",
            secure=True,
            HTTP_HOST="project.dev.readthedocs.io",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Cache-Tag'], 'subproject,subproject:latest')
        self.assertEqual(r['X-RTD-Domain'], 'project.dev.readthedocs.io')
        self.assertEqual(r['X-RTD-Project'], 'subproject')

        # I think it's not accurate saying that it's `subdomain` the method
        # that we use to get the project slug here, since it was in fact the
        # URL's path but we don't have that feature built
        self.assertEqual(r["X-RTD-Project-Method"], "public_domain")

        self.assertEqual(r['X-RTD-Version'], 'latest')
        self.assertEqual(r['X-RTD-version-Method'], 'path')
        self.assertEqual(r['X-RTD-Path'], '/proxito/media/html/subproject/latest/index.html')

    def test_404_headers(self):
        r = self.client.get(
            "/foo/bar.html", secure=True, HTTP_HOST="project.dev.readthedocs.io"
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
        hostname = 'docs.random.com'
        self.domain = fixture.get(
            Domain,
            project=self.project,
            domain=hostname,
        )
        r = self.client.get("/en/latest/", HTTP_HOST=hostname)
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

    def test_footer_headers(self):
        version = self.project.versions.get(slug=LATEST)
        url = (
            reverse('footer_html') +
            f'?project={self.project.slug}&version={version.slug}'
        )
        r = self.client.get(url, HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Cache-Tag'], 'project,project:latest,project:rtd-footer')

    def test_user_domain_headers(self):
        hostname = 'docs.domain.com'
        self.domain = fixture.get(
            Domain,
            project=self.project,
            domain=hostname,
        )
        http_header = 'X-My-Header'
        http_header_secure = 'X-My-Secure-Header'
        http_header_value = 'Header Value; Another Value;'
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

        r = self.client.get("/en/latest/", HTTP_HOST=hostname)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[http_header], http_header_value)
        self.assertFalse(r.has_header(http_header_secure))

        r = self.client.get("/en/latest/", HTTP_HOST=hostname, secure=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r[http_header], http_header_value)
        self.assertEqual(r[http_header_secure], http_header_value)

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cache_headers_public_version_with_private_projects_not_allowed(self):
        r = self.client.get(
            "/en/latest/", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_cache_headers_public_version_with_private_projects_allowed(self):
        r = self.client.get(
            "/en/latest/", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cache_headers_robots_txt_with_private_projects_not_allowed(self):
        r = self.client.get("/robots.txt", HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")
        self.assertEqual(r["Cache-Tag"], "project,project:robots.txt")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_cache_headers_robots_txt_with_private_projects_allowed(self):
        r = self.client.get("/robots.txt", HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")
        self.assertEqual(r["Cache-Tag"], "project,project:robots.txt")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cache_headers_robots_txt_with_private_projects_not_allowed(self):
        r = self.client.get("/sitemap.xml", HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")
        self.assertEqual(r["Cache-Tag"], "project,project:sitemap.xml")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_cache_headers_robots_txt_with_private_projects_allowed(self):
        r = self.client.get("/sitemap.xml", HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["CDN-Cache-Control"], "public")
        self.assertEqual(r["Cache-Tag"], "project,project:sitemap.xml")


class ProxitoV2HeaderTests(ProxitoHeaderTests):
    # TODO: remove this class once the new implementation is the default.
    def setUp(self):
        super().setUp()
        get(
            Feature,
            feature_id=Feature.USE_UNRESOLVER_WITH_PROXITO,
            default_true=True,
            future_default_true=True,
        )
