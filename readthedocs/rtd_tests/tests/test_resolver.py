from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.models import Project, Domain
from readthedocs.rtd_tests.utils import create_user
from readthedocs.core.resolver import base_resolve, resolve, smart_resolve

from django_dynamic_fixture import get


class ResolverBase(TestCase):

    def setUp(self):
        self.owner = create_user(username='owner', password='test')
        self.tester = create_user(username='tester', password='test')
        self.pip = get(Project, slug='pip', users=[self.owner], main_language_project=None)
        self.subproject = get(Project, slug='sub', language='ja', users=[self.owner], main_language_project=None)
        self.translation = get(Project, slug='trans', language='ja', users=[self.owner], main_language_project=None)
        self.pip.add_subproject(self.subproject)
        self.pip.translations.add(self.translation)


class SmartResolverTests(ResolverBase):

    def test_smart_resolver_filename(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.pip, filename='/foo/bar/blah.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar/blah.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.pip, filename='/foo/bar/blah.html')
            self.assertEqual(url, '/en/latest/foo/bar/blah.html')

        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.pip, filename='foo/bar/blah.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar/blah.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.pip, filename='foo/bar/blah.html')
            self.assertEqual(url, '/en/latest/foo/bar/blah.html')

        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.pip, filename='')
            self.assertEqual(url, '/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.pip, filename='')
            self.assertEqual(url, '/en/latest/')

    def test_smart_resolver_subdomain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.pip, filename='index.html')
            self.assertEqual(url, '/docs/pip/en/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/index.html')

    def test_smart_resolver_domain_object(self):
        self.domain = get(Domain, url='http://docs.foobar.com', project=self.pip)
        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/index.html')

    def test_smart_resolver_subproject_subdomain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/ja/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/ja/latest/index.html')

    def test_smart_resolver_subproject_single_version(self):
        self.subproject.single_version = True
        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/index.html')

    def test_smart_resolver_subproject_both_single_version(self):
        self.pip.single_version = True
        self.subproject.single_version = True
        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/index.html')

    def test_smart_resolver_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = smart_resolve(project=self.translation, filename='index.html')
            self.assertEqual(url, '/docs/pip/ja/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = smart_resolve(project=self.translation, filename='index.html')
            self.assertEqual(url, '/ja/latest/index.html')


class ResolverTests(ResolverBase):

    def test_resolver_force_single_version(self):
        self.pip.single_version = False
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, filename='index.html', single_version=True)
            self.assertEqual(url, '/docs/pip/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, filename='index.html', single_version=True)
            self.assertEqual(url, '/index.html')

    def test_resolver_force_domain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, filename='index.html', cname=True)
            self.assertEqual(url, '/en/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, filename='index.html', cname=True)
            self.assertEqual(url, '/en/latest/index.html')

    def test_resolver_force_domain_single_version(self):
        self.pip.single_version = False
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, filename='index.html', single_version=True, cname=True)
            self.assertEqual(url, '/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, filename='index.html', single_version=True, cname=True)
            self.assertEqual(url, '/index.html')

    def test_resolver_force_language(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, filename='index.html', language='cz')
            self.assertEqual(url, '/docs/pip/cz/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, filename='index.html', language='cz')
            self.assertEqual(url, '/cz/latest/index.html')

    def test_resolver_force_version(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, filename='index.html', version_slug='foo')
            self.assertEqual(url, '/docs/pip/en/foo/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, filename='index.html', version_slug='foo')
            self.assertEqual(url, '/en/foo/index.html')

    def test_resolver_force_language_version(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, filename='index.html', language='cz', version_slug='foo')
            self.assertEqual(url, '/docs/pip/cz/foo/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, filename='index.html', language='cz', version_slug='foo')
            self.assertEqual(url, '/cz/foo/index.html')

    def test_resolver_no_force_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.translation, filename='index.html', language='cz')
            self.assertEqual(url, '/docs/pip/ja/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.translation, filename='index.html', language='cz')
            self.assertEqual(url, '/ja/latest/index.html')

    def test_resolver_no_force_translation_with_version(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.translation, filename='index.html', language='cz', version_slug='foo')
            self.assertEqual(url, '/docs/pip/ja/foo/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.translation, filename='index.html', language='cz', version_slug='foo')
            self.assertEqual(url, '/ja/foo/index.html')
