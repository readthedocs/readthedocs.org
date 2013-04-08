from django.core.urlresolvers import reverse
from django.core.urlresolvers import NoReverseMatch
from django.test import TestCase


class URLTests(TestCase):

    def test_wipe_no_params(self):
        try:
            reverse('wipe_version')
            self.fail('reverse with no parameters should fail')
        except NoReverseMatch:
            pass

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
