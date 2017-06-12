from __future__ import absolute_import
from django.core.urlresolvers import reverse
from django.core.urlresolvers import NoReverseMatch
from django.test import TestCase


class WipeUrlTests(TestCase):

    def test_wipe_no_params(self):
        with self.assertRaises(NoReverseMatch):
            reverse('wipe_version')

    def test_wipe_alphabetic(self):
        project_slug = 'alphabetic'
        version = 'version'
        url = reverse('wipe_version', args=[project_slug, version])
        self.assertEqual(url, '/wipe/alphabetic/version/')

    def test_wipe_alphanumeric(self):
        project_slug = 'alpha123'
        version = '123alpha'
        url = reverse('wipe_version', args=[project_slug, version])
        self.assertEqual(url, '/wipe/alpha123/123alpha/')

    def test_wipe_underscore_hyphen(self):
        project_slug = 'alpha_123'
        version = '123-alpha'
        url = reverse('wipe_version', args=[project_slug, version])
        self.assertEqual(url, '/wipe/alpha_123/123-alpha/')

    def test_wipe_version_dot(self):
        project_slug = 'alpha-123'
        version = '1.2.3'
        url = reverse('wipe_version', args=[project_slug, version])
        self.assertEqual(url, '/wipe/alpha-123/1.2.3/')

    def test_wipe_version_start_dot(self):
        project_slug = 'alpha-123'
        version = '.2.3'
        try:
            reverse('wipe_version', args=[project_slug, version])
        except NoReverseMatch:
            pass


class TestVersionURLs(TestCase):

    def test_version_url_with_caps(self):
        url = reverse(
            'project_download_media',
            kwargs={'type_': 'pdf', 'version_slug': u'1.4.X', 'project_slug': u'django'}
        )
        self.assertTrue(url)
