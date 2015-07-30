import json
import mock

from django.test import TestCase

from rtd_tests.mocks.paths import fake_paths_by_regex
from projects.models import Project


class Testmaker(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.latest = self.pip.versions.create_latest()

    def test_footer(self):
        r = self.client.get('/api/v2/footer_html/?project=pip&version=latest&page=index', {})
        resp = json.loads(r.content)
        self.assertEqual(resp['version_active'], True)
        self.assertEqual(resp['version_compare']['is_highest'], True)
        self.assertEqual(resp['version_supported'], True)
        self.assertEqual(r.context['main_project'], self.pip)
        self.assertEqual(r.status_code, 200)

        self.latest.active = False
        self.latest.save()
        r = self.client.get('/api/v2/footer_html/?project=pip&version=latest&page=index', {})
        resp = json.loads(r.content)
        self.assertEqual(resp['version_active'], False)
        self.assertEqual(r.status_code, 200)

    def test_footer_uses_version_compare(self):
        version_compare = 'restapi.views.footer_views.get_version_compare_data'
        with mock.patch(version_compare) as get_version_compare_data:
            get_version_compare_data.return_value = {
                'MOCKED': True
            }

            r = self.client.get('/api/v2/footer_html/?project=pip&version=latest&page=index', {})
            self.assertEqual(r.status_code, 200)

            resp = json.loads(r.content)
            self.assertEqual(resp['version_compare'], {'MOCKED': True})

    def test_pdf_build_mentioned_in_footer(self):
        with fake_paths_by_regex('\.pdf$'):
            response = self.client.get(
                '/api/v2/footer_html/?project=pip&version=latest&page=index', {})
        self.assertContains(response, 'pdf')

    def test_pdf_not_mentioned_in_footer_when_build_is_disabled(self):
        self.pip.enable_pdf_build = False
        self.pip.save()
        with fake_paths_by_regex('\.pdf$'):
            response = self.client.get(
                '/api/v2/footer_html/?project=pip&version=latest&page=index', {})
        self.assertNotContains(response, 'pdf')

    def test_epub_build_mentioned_in_footer(self):
        with fake_paths_by_regex('\.epub$'):
            response = self.client.get(
                '/api/v2/footer_html/?project=pip&version=latest&page=index', {})
        self.assertContains(response, 'epub')

    def test_epub_not_mentioned_in_footer_when_build_is_disabled(self):
        self.pip.enable_epub_build = False
        self.pip.save()
        with fake_paths_by_regex('\.epub$'):
            response = self.client.get(
                '/api/v2/footer_html/?project=pip&version=latest&page=index', {})
        self.assertNotContains(response, 'epub')
