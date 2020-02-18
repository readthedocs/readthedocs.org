# Copied from .org test_redirects


from django.test import override_settings

from .base import BaseDocServing


@override_settings(PUBLIC_DOMAIN_USES_HTTPS=True)
class RedirectTests(BaseDocServing):

    def test_root_url(self):
        r = self.client.get('/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/en/latest/',
        )

    def test_subproject_root_url(self):
        r = self.client.get('/projects/subproject/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'https://project.dev.readthedocs.io/projects/subproject/en/latest/',
        )

    def test_root_redirect_with_query_params(self):
        r = self.client.get('/?foo=bar', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'https://project.dev.readthedocs.io/en/latest/?foo=bar'
        )

    # Specific Page Redirects
    def test_proper_page_on_subdomain(self):
        r = self.client.get('/page/test.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'https://project.dev.readthedocs.io/en/latest/test.html',
        )
