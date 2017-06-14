from __future__ import absolute_import
import mock

from rest_framework.test import APIRequestFactory, APITestCase

from readthedocs.core.middleware import FooterNoSessionMiddleware
from readthedocs.rtd_tests.mocks.paths import fake_paths_by_regex
from readthedocs.projects.models import Project
from readthedocs.restapi.views.footer_views import footer_html


class Testmaker(APITestCase):
    fixtures = ['test_data']
    url = '/api/v2/footer_html/?project=pip&version=latest&page=index'
    factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        cls.pip = Project.objects.get(slug='pip')
        cls.latest = cls.pip.versions.create_latest()

    def render(self):
        request = self.factory.get(self.url)
        response = footer_html(request)
        response.render()
        return response

    def test_footer(self):
        r = self.client.get(self.url)
        self.assertTrue(r.data['version_active'])
        self.assertTrue(r.data['version_compare']['is_highest'])
        self.assertTrue(r.data['version_supported'])
        self.assertEqual(r.context['main_project'], self.pip)
        self.assertEqual(r.status_code, 200)

        self.latest.active = False
        self.latest.save()
        r = self.render()
        self.assertFalse(r.data['version_active'])
        self.assertEqual(r.status_code, 200)

    def test_footer_uses_version_compare(self):
        version_compare = 'readthedocs.restapi.views.footer_views.get_version_compare_data'
        with mock.patch(version_compare) as get_version_compare_data:
            get_version_compare_data.return_value = {
                'MOCKED': True
            }
            r = self.render()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.data['version_compare'], {'MOCKED': True})

    def test_pdf_build_mentioned_in_footer(self):
        with fake_paths_by_regex('\.pdf$'):
            response = self.render()
        self.assertIn('pdf', response.data['html'])

    def test_pdf_not_mentioned_in_footer_when_build_is_disabled(self):
        self.pip.enable_pdf_build = False
        self.pip.save()
        with fake_paths_by_regex('\.pdf$'):
            response = self.render()
        self.assertNotIn('pdf', response.data['html'])

    def test_epub_build_mentioned_in_footer(self):
        with fake_paths_by_regex('\.epub$'):
            response = self.render()
        self.assertIn('epub', response.data['html'])

    def test_epub_not_mentioned_in_footer_when_build_is_disabled(self):
        self.pip.enable_epub_build = False
        self.pip.save()
        with fake_paths_by_regex('\.epub$'):
            response = self.render()
        self.assertNotIn('epub', response.data['html'])

    def test_no_session_logged_out(self):
        mid = FooterNoSessionMiddleware()

        # Null session here
        request = self.factory.get('/api/v2/footer_html/')
        mid.process_request(request)
        self.assertEqual(request.session, {})

        # Proper session here
        home_request = self.factory.get('/')
        mid.process_request(home_request)
        self.assertEqual(home_request.session.TEST_COOKIE_NAME, 'testcookie')
