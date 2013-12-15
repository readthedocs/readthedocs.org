from django.test import TestCase

from builds.models import Version
from projects.models import Project


class RedirectSingleVersionTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        pip = Project.objects.get(slug='pip')
        pip.single_version = True
        pip.save()
        Version.objects.create(project=pip, identifier='latest',
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
