import mock
from django.contrib.sessions.backends.base import SessionBase
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIRequestFactory, APITestCase

from readthedocs.api.v2.views.footer_views import (
    FooterHTML,
    get_version_compare_data,
)
from readthedocs.builds.constants import BRANCH, LATEST, TAG
from readthedocs.builds.models import Version
from readthedocs.core.middleware import FooterNoSessionMiddleware
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.mocks.paths import fake_paths_by_regex


class Testmaker(APITestCase):
    fixtures = ['test_data']
    url = '/api/v2/footer_html/?project=pip&version=latest&page=index&docroot=/'
    factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        cls.pip = Project.objects.get(slug='pip')
        cls.latest = cls.pip.versions.create_latest()

    def render(self):
        request = self.factory.get(self.url)
        response = FooterHTML.as_view()(request)
        response.render()
        return response

    def test_footer(self):
        r = self.client.get(self.url)
        self.assertTrue(r.data['version_active'])
        self.assertTrue(r.data['version_compare']['is_highest'])
        self.assertTrue(r.data['version_supported'])
        self.assertFalse(r.data['show_version_warning'])
        self.assertEqual(r.context['main_project'], self.pip)
        self.assertEqual(r.status_code, 200)

        self.latest.active = False
        self.latest.save()
        r = self.render()
        self.assertFalse(r.data['version_active'])
        self.assertEqual(r.status_code, 200)

    def test_footer_uses_version_compare(self):
        version_compare = 'readthedocs.api.v2.views.footer_views.get_version_compare_data'  # noqa
        with mock.patch(version_compare) as get_version_compare_data:
            get_version_compare_data.return_value = {
                'MOCKED': True,
            }
            r = self.render()
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.data['version_compare'], {'MOCKED': True})

    def test_pdf_build_mentioned_in_footer(self):
        with fake_paths_by_regex(r'\.pdf$'):
            response = self.render()
        self.assertIn('pdf', response.data['html'])

    def test_pdf_not_mentioned_in_footer_when_doesnt_exists(self):
        with fake_paths_by_regex(r'\.pdf$', exists=False):
            response = self.render()
        self.assertNotIn('pdf', response.data['html'])

    def test_epub_build_mentioned_in_footer(self):
        with fake_paths_by_regex(r'\.epub$'):
            response = self.render()
        self.assertIn('epub', response.data['html'])

    def test_epub_not_mentioned_in_footer_when_doesnt_exists(self):
        with fake_paths_by_regex(r'\.epub$', exists=False):
            response = self.render()
        self.assertNotIn('epub', response.data['html'])

    def test_no_session_logged_out(self):
        mid = FooterNoSessionMiddleware()

        # Null session here
        request = self.factory.get('/api/v2/footer_html/')
        mid.process_request(request)
        self.assertIsInstance(request.session, SessionBase)
        self.assertEqual(list(request.session.keys()), [])

        # Proper session here
        home_request = self.factory.get('/')
        mid.process_request(home_request)
        self.assertEqual(home_request.session.TEST_COOKIE_NAME, 'testcookie')

    def test_show_version_warning(self):
        self.pip.show_version_warning = True
        self.pip.save()
        response = self.render()
        self.assertTrue(response.data['show_version_warning'])

    def test_show_edit_on_github(self):
        version = self.pip.versions.get(slug=LATEST)
        version.type = BRANCH
        version.save()
        response = self.render()
        self.assertIn('On GitHub', response.data['html'])
        self.assertIn('View', response.data['html'])
        self.assertIn('Edit', response.data['html'])

    def test_not_show_edit_on_github(self):
        version = self.pip.versions.get(slug=LATEST)
        version.type = TAG
        version.save()
        response = self.render()
        self.assertIn('On GitHub', response.data['html'])
        self.assertIn('View', response.data['html'])
        self.assertNotIn('Edit', response.data['html'])


@override_settings(
    USE_SUBDOMAIN=True,
    PUBLIC_DOMAIN='readthedocs.io',
)
class TestVersionCompareFooter(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')
        self.pip.versions.update(built=True)

    def test_highest_version_from_stable(self):
        base_version = self.pip.get_stable_version()
        valid_data = {
            'project': 'Version 0.8.1 of Pip (19)',
            'url': 'http://pip.readthedocs.io/en/0.8.1/',
            'slug': '0.8.1',
            'version': '0.8.1',
            'is_highest': True,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)

    def test_highest_version_from_lower(self):
        base_version = self.pip.versions.get(slug='0.8')
        valid_data = {
            'project': 'Version 0.8.1 of Pip (19)',
            'url': 'http://pip.readthedocs.io/en/0.8.1/',
            'slug': '0.8.1',
            'version': '0.8.1',
            'is_highest': False,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)

    def test_highest_version_from_latest(self):
        Version.objects.create_latest(project=self.pip, built=True)
        base_version = self.pip.versions.get(slug=LATEST)
        valid_data = {
            'project': 'Version 0.8.1 of Pip (19)',
            'url': 'http://pip.readthedocs.io/en/0.8.1/',
            'slug': '0.8.1',
            'version': '0.8.1',
            'is_highest': True,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)

    def test_highest_version_over_branches(self):
        Version.objects.create(
            project=self.pip,
            verbose_name='2.0.0',
            identifier='2.0.0',
            type=BRANCH,
            active=True,
        )

        version = Version.objects.create(
            project=self.pip,
            verbose_name='1.0.0',
            identifier='1.0.0',
            type=TAG,
            active=True,
            built=True,
        )

        base_version = self.pip.versions.get(slug='0.8.1')
        valid_data = {
            'project': 'Version 1.0.0 of Pip ({})'.format(version.pk),
            'url': 'http://pip.readthedocs.io/en/1.0.0/',
            'slug': '1.0.0',
            'version': '1.0.0',
            'is_highest': False,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)

    def test_highest_version_without_tags(self):
        self.pip.versions.filter(type=TAG).update(type=BRANCH)

        base_version = self.pip.versions.get(slug='0.8.1')
        valid_data = {
            'project': 'Version 0.8.1 of Pip (19)',
            'url': 'http://pip.readthedocs.io/en/0.8.1/',
            'slug': '0.8.1',
            'version': '0.8.1',
            'is_highest': True,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)

        base_version = self.pip.versions.get(slug='0.8')
        valid_data = {
            'project': 'Version 0.8.1 of Pip (19)',
            'url': 'http://pip.readthedocs.io/en/0.8.1/',
            'slug': '0.8.1',
            'version': '0.8.1',
            'is_highest': False,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)

        version = Version.objects.create(
            project=self.pip,
            verbose_name='2.0.0',
            identifier='2.0.0',
            type=BRANCH,
            active=True,
            built=True,
        )
        valid_data = {
            'project': 'Version 2.0.0 of Pip ({})'.format(version.pk),
            'url': 'http://pip.readthedocs.io/en/2.0.0/',
            'slug': '2.0.0',
            'version': '2.0.0',
            'is_highest': False,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)


class TestFooterPerformance(APITestCase):
    fixtures = ['test_data']
    url = '/api/v2/footer_html/?project=pip&version=latest&page=index&docroot=/'
    factory = APIRequestFactory()

    # The expected number of queries for generating the footer
    # This shouldn't increase unless we modify the footer API
    EXPECTED_QUERIES = 13

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')
        self.pip.versions.create_latest()
        self.pip.versions.update(built=True)

    def render(self):
        request = self.factory.get(self.url)
        response = FooterHTML.as_view()(request)
        response.render()
        return response

    def test_version_queries(self):
        # The number of Versions shouldn't impact the number of queries
        with self.assertNumQueries(self.EXPECTED_QUERIES):
            response = self.render()
            self.assertContains(response, '0.8.1')

        for patch in range(3):
            identifier = '0.99.{}'.format(patch)
            self.pip.versions.create(
                verbose_name=identifier,
                identifier=identifier,
                type=TAG,
                active=True,
            )

        with self.assertNumQueries(self.EXPECTED_QUERIES):
            response = self.render()
            self.assertContains(response, '0.99.0')

    def test_domain_queries(self):
        # Setting up a custom domain shouldn't impact the number of queries
        self.pip.domains.create(
            domain='http://docs.foobar.com',
            canonical=True,
        )

        with self.assertNumQueries(self.EXPECTED_QUERIES):
            response = self.render()
            self.assertContains(response, 'docs.foobar.com')
