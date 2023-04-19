# Copied from .org test_redirects
from django.test import override_settings
from django_dynamic_fixture import get

from readthedocs.projects.models import Feature
from readthedocs.proxito.constants import RedirectType
from readthedocs.subscriptions.constants import TYPE_CNAME

from .base import BaseDocServing


@override_settings(
    PUBLIC_DOMAIN='dev.readthedocs.io',
    PUBLIC_DOMAIN_USES_HTTPS=True,
    RTD_DEFAULT_FEATURES={
        TYPE_CNAME: 1,
    },
)
class RedirectTests(BaseDocServing):

    def test_root_url_no_slash(self):
        r = self.client.get("", secure=True, HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

    def test_root_url(self):
        r = self.client.get("/", secure=True, HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

    def test_custom_domain_root_url(self):
        self.domain.canonical = True
        self.domain.save()

        r = self.client.get('/', HTTP_HOST=self.domain.domain, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/en/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

    def test_custom_domain_root_url_no_slash(self):
        self.domain.canonical = True
        self.domain.save()

        r = self.client.get('', HTTP_HOST=self.domain.domain, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/en/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

    def test_single_version_root_url_doesnt_redirect(self):
        self.project.single_version = True
        self.project.save()
        r = self.client.get("/", secure=True, HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 200)

    def test_subproject_root_url(self):
        r = self.client.get(
            "/projects/subproject/", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

    def test_subproject_root_url_no_slash(self):
        r = self.client.get(
            "/projects/subproject", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

    def test_single_version_subproject_root_url_no_slash(self):
        self.subproject.single_version = True
        self.subproject.save()
        r = self.client.get(
            "/projects/subproject", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject,subproject:latest")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

    def test_subproject_redirect(self):
        r = self.client.get("/", secure=True, HTTP_HOST="subproject.dev.readthedocs.io")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "https://project.dev.readthedocs.io/projects/subproject/",
        )

        r = self.client.get(
            "/projects/subproject/", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "https://project.dev.readthedocs.io/projects/subproject/en/latest/",
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

        r = self.client.get(
            "/en/latest/", secure=True, HTTP_HOST="subproject.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(
            r.headers["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
        )

        r = self.client.get(
            "/en/latest/foo/bar", secure=True, HTTP_HOST="subproject.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/foo/bar',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(
            r.headers["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
        )

        self.domain.canonical = True
        self.domain.save()
        r = self.client.get(
            "/en/latest/foo/bar", secure=True, HTTP_HOST="subproject.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://docs1.example.com/projects/subproject/en/latest/foo/bar',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(
            r.headers["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
        )

    def test_single_version_subproject_redirect(self):
        self.subproject.single_version = True
        self.subproject.save()

        r = self.client.get("/", secure=True, HTTP_HOST="subproject.dev.readthedocs.io")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(
            r.headers["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
        )

        r = self.client.get(
            "/foo/bar/", secure=True, HTTP_HOST="subproject.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/foo/bar/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(
            r.headers["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
        )

        self.domain.canonical = True
        self.domain.save()
        r = self.client.get(
            "/foo/bar", secure=True, HTTP_HOST="subproject.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://docs1.example.com/projects/subproject/foo/bar',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "subproject")
        self.assertEqual(
            r.headers["X-RTD-Redirect"], RedirectType.subproject_to_main_domain.name
        )

    def test_root_redirect_with_query_params(self):
        r = self.client.get(
            "/?foo=bar", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'https://project.dev.readthedocs.io/en/latest/?foo=bar'
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r.headers["X-RTD-Redirect"], RedirectType.system.name)

    def test_canonicalize_https_redirect(self):
        self.domain.canonical = True
        self.domain.save()

        r = self.client.get('/', HTTP_HOST=self.domain.domain)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Redirect"], RedirectType.http_to_https.name)

        # We should redirect before 404ing
        r = self.client.get('/en/latest/404after302', HTTP_HOST=self.domain.domain)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/en/latest/404after302',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Redirect"], RedirectType.http_to_https.name)

    def test_canonicalize_public_domain_to_cname_redirect(self):
        """Redirect to the CNAME if it is canonical."""
        self.domain.canonical = True
        self.domain.save()

        r = self.client.get("/", secure=True, HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Redirect"], RedirectType.to_canonical_domain.name)

        # We should redirect before 404ing
        r = self.client.get(
            "/en/latest/404after302",
            secure=True,
            HTTP_HOST="project.dev.readthedocs.io",
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/en/latest/404after302',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Redirect"], RedirectType.to_canonical_domain.name)

    def test_translation_redirect(self):
        r = self.client.get(
            "/", secure=True, HTTP_HOST="translation.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://project.dev.readthedocs.io/es/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "translation")
        self.assertEqual(r["X-RTD-Redirect"], RedirectType.system.name)

    def test_translation_secure_redirect(self):
        r = self.client.get('/', HTTP_HOST='translation.dev.readthedocs.io', secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://project.dev.readthedocs.io/es/latest/',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "translation")
        self.assertEqual(r["X-RTD-Redirect"], RedirectType.system.name)

    # Specific Page Redirects
    def test_proper_page_on_subdomain(self):
        r = self.client.get(
            "/page/test.html", secure=True, HTTP_HOST="project.dev.readthedocs.io"
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'https://project.dev.readthedocs.io/en/latest/test.html',
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Redirect"], RedirectType.system.name)

    def test_slash_redirect(self):
        host = 'project.dev.readthedocs.io'

        url = '/en/latest////awesome.html'
        resp = self.client.get(url, secure=True, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome.html',
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

        url = '/en/latest////awesome.html'
        resp = self.client.get(url, secure=True, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome.html',
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

        url = '/en/latest////awesome///index.html'
        resp = self.client.get(url, secure=True, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome/index.html',
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

        url = '/en/latest////awesome///index.html?foo=bar'
        resp = self.client.get(url, secure=True, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome/index.html?foo=bar',
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

        url = '/en/latest////awesome///'
        resp = self.client.get(url, secure=True, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome/',
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

        # Don't change the values of params
        url = '/en/latest////awesome///index.html?foo=bar//bas'
        resp = self.client.get(url, secure=True, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome/index.html?foo=bar//bas',
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

        # WARNING
        # The test client strips multiple slashes at the front of the URL
        # Additional tests for this are in ``test_middleware:test_front_slash``

    def test_https_public_domain_https_redirect(self):
        paths = ["/", "/en/latest/", "/not-found"]
        for path in paths:
            r = self.client.get(
                path, secure=False, HTTP_HOST="project.dev.readthedocs.io"
            )
            self.assertEqual(r.status_code, 302)
            self.assertEqual(
                r["Location"],
                f"https://project.dev.readthedocs.io{path}",
            )
            self.assertEqual(r.headers["CDN-Cache-Control"], "public")
            self.assertEqual(r.headers["Cache-Tag"], "project")
            self.assertEqual(r["X-RTD-Redirect"], RedirectType.http_to_https.name)

    @override_settings(PUBLIC_DOMAIN_USES_HTTPS=False)
    def test_http_public_domain_https_redirect(self):
        r = self.client.get("", secure=False, HTTP_HOST="project.dev.readthedocs.io")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/",
        )
        self.assertEqual(r.headers["CDN-Cache-Control"], "public")
        self.assertEqual(r.headers["Cache-Tag"], "project")
        self.assertEqual(r["X-RTD-Redirect"], RedirectType.system.name)


class ProxitoV2RedirectTests(RedirectTests):
    # TODO: remove this class once the new implementation is the default.
    def setUp(self):
        super().setUp()
        get(
            Feature,
            feature_id=Feature.USE_UNRESOLVER_WITH_PROXITO,
            default_true=True,
            future_default_true=True,
        )
