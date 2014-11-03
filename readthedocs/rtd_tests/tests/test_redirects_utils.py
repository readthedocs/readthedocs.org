from django.test import TestCase
from django.test.utils import override_settings
from projects.models import Project
from django.core.urlresolvers import reverse

from redirects.utils import redirect_filename


class RedirectFilenameTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.proj = Project.objects.get(slug="read-the-docs")

    def test_http_filenames_return_themselves(self):
        self.assertEqual(
            redirect_filename(None, 'http'),
            'http'
        )

    def test_redirects_no_subdomain(self):
        self.assertEqual(
            redirect_filename(self.proj, 'index.html'),
            '/docs/read-the-docs/en/latest/index.html'
        )

    @override_settings(
        USE_SUBDOMAIN=True, PRODUCTION_DOMAIN='rtfd.org'
    )
    def test_redirects_with_subdomain(self):
        self.assertEqual(
            redirect_filename(self.proj, 'faq.html'),
            'http://read-the-docs.rtfd.org/en/latest/faq.html'
        )

    @override_settings(
        USE_SUBDOMAIN=True, PRODUCTION_DOMAIN='rtfd.org'
    )
    def test_single_version_with_subdomain(self):
        self.proj.single_version = True
        self.assertEqual(
            redirect_filename(self.proj, 'faq.html'),
            'http://read-the-docs.rtfd.org/faq.html'
        )

    def test_single_version_no_subdomain(self):
        self.proj.single_version = True
        self.assertEqual(
            redirect_filename(self.proj, 'faq.html'),
            reverse(
                'docs_detail',
                kwargs={
                    'project_slug': self.proj.slug,
                    'filename': 'faq.html',
                }
            )
        )
