from django.core.urlresolvers import reverse
from django.core.urlresolvers import NoReverseMatch
from django.test import TestCase

import core.views

class SubdomainUrlTests(TestCase):

    def test_sub_index(self):
        url = reverse(core.views.subdomain_handler,
            urlconf='core.subdomain_urls')
        self.assertEqual(url, '/')

    def test_sub_lang_version(self):
        url = reverse('docs_detail', urlconf='core.subdomain_urls',
            kwargs={'lang_slug': 'en', 'version_slug': 'latest'})
        self.assertEqual(url, '/en/latest/')

    def test_sub_lang_version_filename(self):
        url = reverse('docs_detail', urlconf='core.subdomain_urls',
            args=['en', 'latest', 'index.html'])
        self.assertEqual(url, '/en/latest/index.html')

    def test_sub_project_full_path(self):
        url = reverse('subproject_docs_detail',
            urlconf='core.subdomain_urls',
            kwargs={'project_slug':'pyramid', 'lang_slug': 'en',
                    'version_slug':'latest', 'filename': 'index.html'})
        self.assertEqual(url, '/projects/pyramid/en/latest/index.html')

    def test_sub_project_slug_only(self):
        url = reverse('subproject_docs_detail',
            urlconf='core.subdomain_urls',
            kwargs={'project_slug': 'pyramid'})
        self.assertEqual(url, '/projects/pyramid')

    def test_sub_page(self):
        url = reverse('docs_detail',
            urlconf='core.subdomain_urls',
            kwargs={'filename': 'install.html'})
        self.assertEqual(url, '/page/install.html')

    def test_sub_version(self):
        url = reverse('version_subdomain_handler',
            urlconf='core.subdomain_urls',
            kwargs={'version_slug': '1.4.1'})
        self.assertEqual(url, '/1.4.1/')

    def test_sub_lang(self):
        url = reverse('lang_subdomain_handler',
            urlconf='core.subdomain_urls',
            kwargs={'lang_slug': 'en'})
        self.assertEqual(url, '/en/')


class WipeUrlTests(TestCase):

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
