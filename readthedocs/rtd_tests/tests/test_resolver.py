from __future__ import absolute_import
import mock

from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import Project, Domain
from readthedocs.rtd_tests.utils import create_user
from readthedocs.core.resolver import resolve_path, resolve, resolve_domain

from django_dynamic_fixture import get


@override_settings(PUBLIC_DOMAIN='readthedocs.org')
class ResolverBase(TestCase):

    def setUp(self):
        with mock.patch('readthedocs.projects.models.broadcast'):
            self.owner = create_user(username='owner', password='test')
            self.tester = create_user(username='tester', password='test')
            self.pip = get(Project, slug='pip', users=[self.owner], main_language_project=None)
            self.subproject = get(Project, slug='sub', language='ja', users=[self.owner], main_language_project=None)
            self.translation = get(Project, slug='trans', language='ja', users=[self.owner], main_language_project=None)
            self.pip.add_subproject(self.subproject)
            self.pip.translations.add(self.translation)


class SmartResolverPathTests(ResolverBase):

    def test_resolver_filename(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='/foo/bar/blah.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar/blah.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='/foo/bar/blah.html')
            self.assertEqual(url, '/en/latest/foo/bar/blah.html')

        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='')
            self.assertEqual(url, '/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='')
            self.assertEqual(url, '/en/latest/')

    def test_resolver_filename_index(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='foo/bar/index.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar/')
            url = resolve_path(project=self.pip, filename='foo/index/index.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/index/')

    def test_resolver_filename_false_index(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='foo/foo_index.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/foo_index.html')
            url = resolve_path(project=self.pip, filename='foo_index/foo_index.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo_index/foo_index.html')

    def test_resolver_filename_sphinx(self):
        self.pip.documentation_type = 'sphinx'
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='foo/bar')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar.html')
            url = resolve_path(project=self.pip, filename='foo/index')
            self.assertEqual(url, '/docs/pip/en/latest/foo/')
        self.pip.documentation_type = 'mkdocs'
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='foo/bar')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar/')
            url = resolve_path(project=self.pip, filename='foo/index')
            self.assertEqual(url, '/docs/pip/en/latest/foo/')

    def test_resolver_subdomain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html')
            self.assertEqual(url, '/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/')

    def test_resolver_domain_object(self):
        self.domain = get(Domain, domain='http://docs.foobar.com', project=self.pip, canonical=True)
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/')

    def test_resolver_domain_object_not_canonical(self):
        self.domain = get(Domain, domain='http://docs.foobar.com', project=self.pip, canonical=False)
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='')
            self.assertEqual(url, '/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='')
            self.assertEqual(url, '/en/latest/')

    def test_resolver_subproject_subdomain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/ja/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/ja/latest/')

    def test_resolver_subproject_single_version(self):
        self.subproject.single_version = True
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/')

    def test_resolver_subproject_both_single_version(self):
        self.pip.single_version = True
        self.subproject.single_version = True
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/')

    def test_resolver_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.translation, filename='index.html')
            self.assertEqual(url, '/docs/pip/ja/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.translation, filename='index.html')
            self.assertEqual(url, '/ja/latest/')


class ResolverPathOverrideTests(ResolverBase):

    """Tests to make sure we can override resolve_path correctly"""

    def test_resolver_force_single_version(self):
        self.pip.single_version = False
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html', single_version=True)
            self.assertEqual(url, '/docs/pip/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html', single_version=True)
            self.assertEqual(url, '/')

    def test_resolver_force_domain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html', cname=True)
            self.assertEqual(url, '/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html', cname=True)
            self.assertEqual(url, '/en/latest/')

    def test_resolver_force_domain_single_version(self):
        self.pip.single_version = False
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html', single_version=True, cname=True)
            self.assertEqual(url, '/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html', single_version=True, cname=True)
            self.assertEqual(url, '/')

    def test_resolver_force_language(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html', language='cz')
            self.assertEqual(url, '/docs/pip/cz/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html', language='cz')
            self.assertEqual(url, '/cz/latest/')

    def test_resolver_force_version(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html', version_slug='foo')
            self.assertEqual(url, '/docs/pip/en/foo/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html', version_slug='foo')
            self.assertEqual(url, '/en/foo/')

    def test_resolver_force_language_version(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html', language='cz', version_slug='foo')
            self.assertEqual(url, '/docs/pip/cz/foo/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html', language='cz', version_slug='foo')
            self.assertEqual(url, '/cz/foo/')

    def test_resolver_no_force_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.translation, filename='index.html', language='cz')
            self.assertEqual(url, '/docs/pip/ja/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.translation, filename='index.html', language='cz')
            self.assertEqual(url, '/ja/latest/')

    def test_resolver_no_force_translation_with_version(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.translation, filename='index.html', language='cz', version_slug='foo')
            self.assertEqual(url, '/docs/pip/ja/foo/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.translation, filename='index.html', language='cz', version_slug='foo')
            self.assertEqual(url, '/ja/foo/')


class ResolverDomainTests(ResolverBase):

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_domain_resolver(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.pip)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.pip)
            self.assertEqual(url, 'pip.readthedocs.org')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_domain_resolver_with_domain_object(self):
        self.domain = get(Domain, domain='docs.foobar.com', project=self.pip, canonical=True)
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.pip)
            self.assertEqual(url, 'docs.foobar.com')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.pip)
            self.assertEqual(url, 'docs.foobar.com')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_domain_resolver_subproject(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.subproject)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.subproject)
            self.assertEqual(url, 'pip.readthedocs.org')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_domain_resolver_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.translation)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.translation)
            self.assertEqual(url, 'pip.readthedocs.org')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org', PUBLIC_DOMAIN='public.readthedocs.org')
    def test_domain_public(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.translation)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.translation)
            self.assertEqual(url, 'pip.public.readthedocs.org')
        # Private overrides domain
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.translation, private=True)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.translation, private=True)
            self.assertEqual(url, 'pip.public.readthedocs.org')


class ResolverTests(ResolverBase):

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_domain(self):
        self.domain = get(Domain, domain='docs.foobar.com', project=self.pip, canonical=True)
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_subproject(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.subproject)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/projects/sub/ja/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.subproject)
            self.assertEqual(url, 'http://pip.readthedocs.org/projects/sub/ja/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.translation)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/ja/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.translation)
            self.assertEqual(url, 'http://pip.readthedocs.org/ja/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_single_version(self):
        self.pip.single_version = True
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_subproject_alias(self):
        relation = self.pip.subprojects.first()
        relation.alias = 'sub_alias'
        relation.save()
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.subproject)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/projects/sub_alias/ja/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.subproject)
            self.assertEqual(url, 'http://pip.readthedocs.org/projects/sub_alias/ja/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_private_project(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, private=True)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, private=True)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_private_project_override(self):
        self.pip.privacy_level = PRIVATE
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
            url = resolve(project=self.pip, private=False)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')
            url = resolve(project=self.pip, private=False)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_private_version_override(self):
        latest = self.pip.versions.first()
        latest.privacy_level = PRIVATE
        latest.save()
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
            url = resolve(project=self.pip, private=False)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')
            url = resolve(project=self.pip, private=False)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org', PUBLIC_DOMAIN='public.readthedocs.org')
    def test_resolver_public_domain_overrides(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, private=True)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
            url = resolve(project=self.pip, private=False)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, private=True)
            self.assertEqual(url, 'http://pip.public.readthedocs.org/en/latest/')
            url = resolve(project=self.pip, private=False)
            self.assertEqual(url, 'http://pip.public.readthedocs.org/en/latest/')

        # Domain overrides PUBLIC_DOMAIN
        self.domain = get(Domain, domain='docs.foobar.com', project=self.pip, canonical=True)
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip, private=True)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
            url = resolve(project=self.pip, private=False)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip, private=True)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
            url = resolve(project=self.pip, private=False)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
