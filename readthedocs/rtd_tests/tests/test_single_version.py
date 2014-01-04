from django.test import TestCase

from builds.models import Version
from projects.models import Project


class RedirectSingleVersionTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')
        self.pip.single_version = True
        self.pip.save()
        Version.objects.create(project=self.pip, identifier='latest',
                       verbose_name='latest', slug='latest',
                       active=True)

    def test_test_case_project_is_single_version(self):
        self.assertTrue(Project.objects.get(name='Pip').single_version)

    def test_test_case_version_exists(self):
        self.assertTrue(Version.objects.filter(project__name__exact='Pip').get(slug='latest'))

    def test_proper_single_version_url_full_with_filename(self):
        r = self.client.get('/docs/pip/usage.html')
        self.assertEqual(r.status_code, 200)

    def test_improper_single_version_url_nonexistent_project(self):
        r = self.client.get('/docs/nonexistent/blah.html')
        self.assertEqual(r.status_code, 404)

    def test_proper_single_version_url_subdomain(self):
        r = self.client.get('/usage.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 200)

    def test_improper_single_version_url_subdomain(self):
        r = self.client.get('/blah.html', HTTP_HOST='nonexistent.readthedocs.org')
        self.assertEqual(r.status_code, 404)

    def test_docs_url_generation(self):
        
        self.pip.single_version = True
        with self.settings(USE_SUBDOMAIN=False):
            self.assertEqual(self.pip.get_docs_url(), '/docs/pip/')
        with self.settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.pip.get_docs_url(), 'http://pip.readthedocs.org/')

        self.pip.single_version = False
        with self.settings(USE_SUBDOMAIN=False):
            self.assertEqual(self.pip.get_docs_url(), '/docs/pip/en/latest/')
        with self.settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.pip.get_docs_url(), 'http://pip.readthedocs.org/en/latest/')

