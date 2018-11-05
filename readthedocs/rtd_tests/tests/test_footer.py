# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import mock
from django.test import TestCase
from rest_framework.test import APIRequestFactory, APITestCase

from readthedocs.builds.constants import BRANCH, LATEST, TAG
from readthedocs.builds.models import Version
from readthedocs.core.middleware import FooterNoSessionMiddleware
from readthedocs.projects.models import Project
from readthedocs.restapi.views.footer_views import (
    footer_html,
    get_version_compare_data,
)
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
        response = footer_html(request)
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
        version_compare = 'readthedocs.restapi.views.footer_views.get_version_compare_data'  # noqa
        with mock.patch(version_compare) as get_version_compare_data:
            get_version_compare_data.return_value = {
                'MOCKED': True,
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


class TestVersionCompareFooter(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')

    def test_highest_version_from_stable(self):
        base_version = self.pip.get_stable_version()
        valid_data = {
            'project': 'Version 0.8.1 of Pip (19)',
            'url': '/dashboard/pip/version/0.8.1/',
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
            'url': '/dashboard/pip/version/0.8.1/',
            'slug': '0.8.1',
            'version': '0.8.1',
            'is_highest': False,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)

    def test_highest_version_from_latest(self):
        Version.objects.create_latest(project=self.pip)
        base_version = self.pip.versions.get(slug=LATEST)
        valid_data = {
            'project': 'Version 0.8.1 of Pip (19)',
            'url': '/dashboard/pip/version/0.8.1/',
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
        )

        base_version = self.pip.versions.get(slug='0.8.1')
        valid_data = {
            'project': 'Version 1.0.0 of Pip ({})'.format(version.pk),
            'url': '/dashboard/pip/version/1.0.0/',
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
            'url': '/dashboard/pip/version/0.8.1/',
            'slug': '0.8.1',
            'version': '0.8.1',
            'is_highest': True,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)

        base_version = self.pip.versions.get(slug='0.8')
        valid_data = {
            'project': 'Version 0.8.1 of Pip (19)',
            'url': '/dashboard/pip/version/0.8.1/',
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
        )
        valid_data = {
            'project': 'Version 2.0.0 of Pip ({})'.format(version.pk),
            'url': '/dashboard/pip/version/2.0.0/',
            'slug': '2.0.0',
            'version': '2.0.0',
            'is_highest': False,
        }
        returned_data = get_version_compare_data(self.pip, base_version)
        self.assertDictEqual(valid_data, returned_data)
