# Copied from .org test_redirects

import pytest
from django.test import override_settings

from .base import BaseDocServing


@override_settings(
    PUBLIC_DOMAIN='dev.readthedocs.io',
    PUBLIC_DOMAIN_USES_HTTPS=True,
)
class RedirectTests(BaseDocServing):

    def test_root_url_no_slash(self):
        r = self.client.get('', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/',
        )

    def test_root_url(self):
        r = self.client.get('/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/',
        )

    def test_custom_domain_root_url(self):
        self.domain.canonical = True
        self.domain.save()

        r = self.client.get('/', HTTP_HOST=self.domain.domain, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/en/latest/',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'system')

    def test_custom_domain_root_url_no_slash(self):
        self.domain.canonical = True
        self.domain.save()

        r = self.client.get('', HTTP_HOST=self.domain.domain, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/en/latest/',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'system')

    def test_single_version_root_url_doesnt_redirect(self):
        self.project.single_version = True
        self.project.save()
        r = self.client.get('/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 200)

    def test_subproject_root_url(self):
        r = self.client.get('/projects/subproject/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/',
        )

    def test_subproject_root_url_no_slash(self):
        r = self.client.get('/projects/subproject', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/',
        )

    def test_single_version_subproject_root_url_no_slash(self):
        self.subproject.single_version = True
        self.subproject.save()
        r = self.client.get('/projects/subproject', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/',
        )

    def test_subproject_redirect(self):
        r = self.client.get('/', HTTP_HOST='subproject.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/',
        )

        r = self.client.get('/en/latest/', HTTP_HOST='subproject.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/',
        )

        r = self.client.get('/en/latest/foo/bar', HTTP_HOST='subproject.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/foo/bar',
        )

        self.domain.canonical = True
        self.domain.save()
        r = self.client.get('/en/latest/foo/bar', HTTP_HOST='subproject.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://docs1.example.com/projects/subproject/en/latest/foo/bar',
        )

    def test_single_version_subproject_redirect(self):
        self.subproject.single_version = True
        self.subproject.save()

        r = self.client.get('/', HTTP_HOST='subproject.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/',
        )

        r = self.client.get('/foo/bar/', HTTP_HOST='subproject.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/foo/bar/',
        )

        self.domain.canonical = True
        self.domain.save()
        r = self.client.get('/foo/bar', HTTP_HOST='subproject.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://docs1.example.com/projects/subproject/foo/bar',
        )

    def test_root_redirect_with_query_params(self):
        r = self.client.get('/?foo=bar', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'https://project.dev.readthedocs.io/en/latest/?foo=bar'
        )

    def test_canonicalize_https_redirect(self):
        self.domain.canonical = True
        self.domain.save()

        r = self.client.get('/', HTTP_HOST=self.domain.domain)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'https')

        # We should redirect before 404ing
        r = self.client.get('/en/latest/404after302', HTTP_HOST=self.domain.domain)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/en/latest/404after302',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'https')

    def test_canonicalize_public_domain_to_cname_redirect(self):
        """Redirect to the CNAME if it is canonical."""
        self.domain.canonical = True
        self.domain.save()

        r = self.client.get('/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'canonical-cname')

        # We should redirect before 404ing
        r = self.client.get('/en/latest/404after302', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://{self.domain.domain}/en/latest/404after302',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'canonical-cname')

    def test_translation_redirect(self):
        r = self.client.get('/', HTTP_HOST='translation.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://project.dev.readthedocs.io/es/latest/',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'system')

    def test_translation_secure_redirect(self):
        r = self.client.get('/', HTTP_HOST='translation.dev.readthedocs.io', secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], f'https://project.dev.readthedocs.io/es/latest/',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'system')

    # We are not canonicalizing custom domains -> public domain for now
    @pytest.mark.xfail(strict=True)
    def test_canonicalize_cname_to_public_domain_redirect(self):
        """Redirect to the public domain if the CNAME is not canonical."""
        r = self.client.get('/', HTTP_HOST=self.domain.domain)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'noncanonical-cname')

        # We should redirect before 404ing
        r = self.client.get('/en/latest/404after302', HTTP_HOST=self.domain2.domain)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/404after302',
        )
        self.assertEqual(r['X-RTD-Redirect'], 'noncanonical-cname')

    # Specific Page Redirects
    def test_proper_page_on_subdomain(self):
        r = self.client.get('/page/test.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'https://project.dev.readthedocs.io/en/latest/test.html',
        )

    def test_slash_redirect(self):
        host = 'project.dev.readthedocs.io'

        url = '/en/latest////awesome.html'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome.html',
        )

        url = '/en/latest////awesome.html'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome.html',
        )

        url = '/en/latest////awesome///index.html'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome/index.html',
        )

        url = '/en/latest////awesome///index.html?foo=bar'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome/index.html?foo=bar',
        )

        url = '/en/latest////awesome///'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome/',
        )

        # Don't change the values of params
        url = '/en/latest////awesome///index.html?foo=bar//bas'
        resp = self.client.get(url, HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp['Location'], '/en/latest/awesome/index.html?foo=bar//bas',
        )

        # WARNING
        # The test client strips multiple slashes at the front of the URL
        # Additional tests for this are in ``test_middleware:test_front_slash``
