from unittest import mock

import django_dynamic_fixture as fixture
import pytest
from django.test import TestCase, override_settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.resolver import (
    Resolver,
    resolve,
    resolve_domain,
    resolve_path,
)
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import Domain, Project, ProjectRelationship
from readthedocs.rtd_tests.utils import create_user


@override_settings(PUBLIC_DOMAIN='readthedocs.org')
class ResolverBase(TestCase):

    def setUp(self):
        with mock.patch('readthedocs.projects.models.broadcast'):
            self.owner = create_user(username='owner', password='test')
            self.tester = create_user(username='tester', password='test')
            self.pip = fixture.get(
                Project,
                slug='pip',
                users=[self.owner],
                main_language_project=None,
            )
            self.subproject = fixture.get(
                Project,
                slug='sub',
                language='ja',
                users=[self.owner],
                main_language_project=None,
            )
            self.translation = fixture.get(
                Project,
                slug='trans',
                language='ja',
                users=[self.owner],
                main_language_project=None,
            )
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
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar/index.html')
            url = resolve_path(
                project=self.pip, filename='foo/index/index.html',
            )
            self.assertEqual(url, '/docs/pip/en/latest/foo/index/index.html')

    def test_resolver_filename_false_index(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='foo/foo_index.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/foo_index.html')
            url = resolve_path(
                project=self.pip, filename='foo_index/foo_index.html',
            )
            self.assertEqual(
                url, '/docs/pip/en/latest/foo_index/foo_index.html',
            )

    def test_resolver_filename_sphinx(self):
        self.pip.documentation_type = 'sphinx'
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='foo/bar')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar')

            url = resolve_path(project=self.pip, filename='foo/index')
            self.assertEqual(url, '/docs/pip/en/latest/foo/index')

    def test_resolver_filename_mkdocs(self):
        self.pip.documentation_type = 'mkdocs'
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='foo/bar')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar')

            url = resolve_path(project=self.pip, filename='foo/index.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/index.html')

            url = resolve_path(project=self.pip, filename='foo/bar.html')
            self.assertEqual(url, '/docs/pip/en/latest/foo/bar.html')

    def test_resolver_subdomain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html')
            self.assertEqual(url, '/docs/pip/en/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/index.html')

    def test_resolver_domain_object(self):
        self.domain = fixture.get(
            Domain,
            domain='http://docs.foobar.com',
            project=self.pip,
            canonical=True,
        )
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='index.html')
            self.assertEqual(url, '/en/latest/index.html')

    def test_resolver_domain_object_not_canonical(self):
        self.domain = fixture.get(
            Domain,
            domain='http://docs.foobar.com',
            project=self.pip,
            canonical=False,
        )
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.pip, filename='')
            self.assertEqual(url, '/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.pip, filename='')
            self.assertEqual(url, '/en/latest/')

    def test_resolver_subproject_subdomain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/ja/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/ja/latest/index.html')

    def test_resolver_subproject_single_version(self):
        self.subproject.single_version = True
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/index.html')

    def test_resolver_subproject_both_single_version(self):
        self.pip.single_version = True
        self.subproject.single_version = True
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/docs/pip/projects/sub/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.subproject, filename='index.html')
            self.assertEqual(url, '/projects/sub/index.html')

    def test_resolver_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(project=self.translation, filename='index.html')
            self.assertEqual(url, '/docs/pip/ja/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(project=self.translation, filename='index.html')
            self.assertEqual(url, '/ja/latest/index.html')

    def test_resolver_urlconf(self):
        url = resolve_path(project=self.translation, filename='index.html', urlconf='$version/$filename')
        self.assertEqual(url, 'latest/index.html')

    def test_resolver_urlconf_extra(self):
        url = resolve_path(project=self.translation, filename='index.html', urlconf='foo/bar/$version/$filename')
        self.assertEqual(url, 'foo/bar/latest/index.html')

class ResolverPathOverrideTests(ResolverBase):

    """Tests to make sure we can override resolve_path correctly."""

    def test_resolver_force_single_version(self):
        self.pip.single_version = False
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(
                project=self.pip, filename='index.html', single_version=True,
            )
            self.assertEqual(url, '/docs/pip/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(
                project=self.pip, filename='index.html', single_version=True,
            )
            self.assertEqual(url, '/index.html')

    def test_resolver_force_domain(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(
                project=self.pip, filename='index.html', cname=True,
            )
            self.assertEqual(url, '/en/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(
                project=self.pip, filename='index.html', cname=True,
            )
            self.assertEqual(url, '/en/latest/index.html')

    def test_resolver_force_domain_single_version(self):
        self.pip.single_version = False
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(
                project=self.pip, filename='index.html', single_version=True,
                cname=True,
            )
            self.assertEqual(url, '/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(
                project=self.pip, filename='index.html', single_version=True,
                cname=True,
            )
            self.assertEqual(url, '/index.html')

    def test_resolver_force_language(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(
                project=self.pip, filename='index.html', language='cz',
            )
            self.assertEqual(url, '/docs/pip/cz/latest/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(
                project=self.pip, filename='index.html', language='cz',
            )
            self.assertEqual(url, '/cz/latest/index.html')

    def test_resolver_force_version(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(
                project=self.pip, filename='index.html', version_slug='foo',
            )
            self.assertEqual(url, '/docs/pip/en/foo/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(
                project=self.pip, filename='index.html', version_slug='foo',
            )
            self.assertEqual(url, '/en/foo/index.html')

    def test_resolver_force_language_version(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_path(
                project=self.pip, filename='index.html', language='cz',
                version_slug='foo',
            )
            self.assertEqual(url, '/docs/pip/cz/foo/index.html')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_path(
                project=self.pip, filename='index.html', language='cz',
                version_slug='foo',
            )
            self.assertEqual(url, '/cz/foo/index.html')


class ResolverCanonicalProject(TestCase):

    def test_project_with_same_translation_and_main_language(self):
        proj1 = fixture.get(Project, main_language_project=None)
        proj2 = fixture.get(Project, main_language_project=None)

        self.assertFalse(proj1.translations.exists())
        self.assertIsNone(proj1.main_language_project)
        self.assertFalse(proj2.translations.exists())
        self.assertIsNone(proj2.main_language_project)

        proj1.translations.add(proj2)
        proj1.main_language_project = proj2
        proj1.save()
        self.assertEqual(
            proj1.main_language_project.main_language_project,
            proj1,
        )

        # This tests that we aren't going to re-recurse back to resolving proj1
        r = Resolver()
        self.assertEqual(r._get_canonical_project(proj1), proj2)

    def test_project_with_same_superproject_and_translation(self):
        proj1 = fixture.get(Project, main_language_project=None)
        proj2 = fixture.get(Project, main_language_project=None)

        self.assertFalse(proj1.translations.exists())
        self.assertIsNone(proj1.main_language_project)
        self.assertFalse(proj2.translations.exists())
        self.assertIsNone(proj2.main_language_project)

        proj2.translations.add(proj1)
        proj2.add_subproject(proj1)
        self.assertEqual(
            proj1.main_language_project,
            proj2,
        )
        self.assertEqual(
            proj1.superprojects.first().parent,
            proj2,
        )

        # This tests that we aren't going to re-recurse back to resolving proj1
        r = Resolver()
        self.assertEqual(r._get_canonical_project(proj1), proj2)

    def test_project_with_same_grandchild_project(self):
        # Note: we don't disallow this, but we also don't support this in our
        # resolution (yet at least)
        proj1 = fixture.get(Project, main_language_project=None)
        proj2 = fixture.get(Project, main_language_project=None)
        proj3 = fixture.get(Project, main_language_project=None)

        self.assertFalse(proj1.translations.exists())
        self.assertFalse(proj2.translations.exists())
        self.assertFalse(proj3.translations.exists())
        self.assertIsNone(proj1.main_language_project)
        self.assertIsNone(proj2.main_language_project)
        self.assertIsNone(proj3.main_language_project)

        proj2.add_subproject(proj1)
        proj3.add_subproject(proj2)
        proj1.add_subproject(proj3)
        self.assertEqual(
            proj1.superprojects.first().parent,
            proj2,
        )
        self.assertEqual(
            proj2.superprojects.first().parent,
            proj3,
        )
        self.assertEqual(
            proj3.superprojects.first().parent,
            proj1,
        )

        # This tests that we aren't going to re-recurse back to resolving proj1
        r = Resolver()
        self.assertEqual(r._get_canonical_project(proj1), proj3)


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
        self.domain = fixture.get(
            Domain,
            domain='docs.foobar.com',
            project=self.pip,
            canonical=True,
        )
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
    def test_domain_resolver_subproject_itself(self):
        """
        Test inconsistent project/subproject relationship.

        If a project is subproject of itself (inconsistent relationship) we
        still resolves the proper domain.
        """
        # remove all possible subproject relationships
        self.pip.subprojects.all().delete()

        # add the project as subproject of itself
        self.pip.add_subproject(self.pip)

        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.pip)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.pip)
            self.assertEqual(url, 'pip.readthedocs.org')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_domain_resolver_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.translation)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.translation)
            self.assertEqual(url, 'pip.readthedocs.org')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_domain_resolver_translation_itself(self):
        """
        Test inconsistent project/translation relationship.

        If a project is a translation of itself (inconsistent relationship) we
        still resolves the proper domain.
        """
        # remove all possible translations relationships
        self.pip.translations.all().delete()

        # add the project as subproject of itself
        self.pip.translations.add(self.pip)

        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.pip)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.pip)
            self.assertEqual(url, 'pip.readthedocs.org')

    @override_settings(
        PRODUCTION_DOMAIN='readthedocs.org',
        PUBLIC_DOMAIN='public.readthedocs.org',
    )
    def test_domain_public(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve_domain(project=self.translation)
            self.assertEqual(url, 'readthedocs.org')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve_domain(project=self.translation)
            self.assertEqual(url, 'pip.public.readthedocs.org')

    @override_settings(
        PRODUCTION_DOMAIN='readthedocs.org',
        PUBLIC_DOMAIN='public.readthedocs.org',
        RTD_EXTERNAL_VERSION_DOMAIN='dev.readthedocs.build',
        PUBLIC_DOMAIN_USES_HTTPS=True,
        USE_SUBDOMAIN=True,
    )
    def test_domain_external(self):
        latest = self.pip.versions.first()
        latest.type = EXTERNAL
        latest.save()
        url = resolve(project=self.pip)
        self.assertEqual(url, 'https://pip--latest.dev.readthedocs.build/en/latest/')
        url = resolve(project=self.pip, version_slug=latest.slug)
        self.assertEqual(url, 'https://pip--latest.dev.readthedocs.build/en/latest/')
        url = resolve(project=self.pip, version_slug='non-external')
        self.assertEqual(url, 'https://pip.public.readthedocs.org/en/non-external/')


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
        self.domain = fixture.get(
            Domain,
            domain='docs.foobar.com',
            project=self.pip,
            canonical=True,
        )
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_domain_https(self):
        self.domain = fixture.get(
            Domain,
            domain='docs.foobar.com',
            project=self.pip,
            https=True,
            canonical=True,
        )
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'https://docs.foobar.com/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'https://docs.foobar.com/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_subproject(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.subproject)
            self.assertEqual(
                url, 'http://readthedocs.org/docs/pip/projects/sub/ja/latest/',
            )
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.subproject)
            self.assertEqual(
                url, 'http://pip.readthedocs.org/projects/sub/ja/latest/',
            )

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_translation(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.translation)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/ja/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.translation)
            self.assertEqual(url, 'http://pip.readthedocs.org/ja/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_nested_translation_of_a_subproject(self):
        """The project is a translation, and the main translation is a subproject of a project."""
        translation = fixture.get(
            Project,
            slug='api-es',
            language='es',
            users=[self.owner],
            main_language_project=self.subproject,
        )

        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=translation)
            self.assertEqual(
                url, 'http://readthedocs.org/docs/pip/projects/sub/es/latest/',
            )
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=translation)
            self.assertEqual(
                url, 'http://pip.readthedocs.org/projects/sub/es/latest/',
            )

    @pytest.mark.xfail(reason='We do not support this for now', strict=True)
    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_nested_subproject_of_a_translation(self):
        """The project is a subproject, and the superproject is a translation of a project."""
        project = fixture.get(
            Project,
            slug='all-docs',
            language='en',
            users=[self.owner],
            main_language_project=None,
        )
        translation = fixture.get(
            Project,
            slug='docs-es',
            language='es',
            users=[self.owner],
            main_language_project=project,
        )

        subproject = fixture.get(
            Project,
            slug='api-es',
            language='es',
            users=[self.owner],
            main_language_project=None,
        )
        translation.add_subproject(subproject)

        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=subproject)
            self.assertEqual(url, 'http://readthedocs.org/docs/docs-es/projects/api-es/es/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=subproject)
            self.assertEqual(url, 'http://docs-es.readthedocs.org/projects/api-es/es/latest/')

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
            self.assertEqual(
                url,
                'http://readthedocs.org/docs/pip/projects/sub_alias/ja/latest/',
            )
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.subproject)
            self.assertEqual(
                url,
                'http://pip.readthedocs.org/projects/sub_alias/ja/latest/',
            )

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_private_project(self):
        self.pip.privacy_level = PRIVATE
        self.pip.save()
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_private_project_override(self):
        self.pip.privacy_level = PRIVATE
        self.pip.save()
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_private_version_override(self):
        latest = self.pip.versions.first()
        latest.privacy_level = PRIVATE
        latest.save()
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.org/en/latest/')

    @override_settings(
        PRODUCTION_DOMAIN='readthedocs.org',
        PUBLIC_DOMAIN='public.readthedocs.org',
    )
    def test_resolver_public_domain_overrides(self):
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(
                url, 'http://pip.public.readthedocs.org/en/latest/',
            )
            url = resolve(project=self.pip)
            self.assertEqual(
                url, 'http://pip.public.readthedocs.org/en/latest/',
            )

        # Domain overrides PUBLIC_DOMAIN
        self.domain = fixture.get(
            Domain,
            domain='docs.foobar.com',
            project=self.pip,
            canonical=True,
        )
        with override_settings(USE_SUBDOMAIN=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
        with override_settings(USE_SUBDOMAIN=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://docs.foobar.com/en/latest/')

    @override_settings(
        PRODUCTION_DOMAIN='readthedocs.org',
        PUBLIC_DOMAIN='readthedocs.io',
        USE_SUBDOMAIN=True,
    )
    def test_resolver_domain_https(self):
        with override_settings(PUBLIC_DOMAIN_USES_HTTPS=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'https://pip.readthedocs.io/en/latest/')

            url = resolve(project=self.pip)
            self.assertEqual(url, 'https://pip.readthedocs.io/en/latest/')

        with override_settings(PUBLIC_DOMAIN_USES_HTTPS=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, 'http://pip.readthedocs.io/en/latest/')


class ResolverAltSetUp:

    def setUp(self):
        with mock.patch('readthedocs.projects.models.broadcast'):
            self.owner = create_user(username='owner', password='test')
            self.tester = create_user(username='tester', password='test')
            self.pip = fixture.get(
                Project,
                slug='pip',
                users=[self.owner],
                main_language_project=None,
            )
            self.seed = fixture.get(
                Project,
                slug='sub',
                users=[self.owner],
                main_language_project=None,
            )
            self.subproject = fixture.get(
                Project,
                slug='subproject',
                language='ja',
                users=[self.owner],
                main_language_project=None,
            )
            self.translation = fixture.get(
                Project,
                slug='trans',
                language='ja',
                users=[self.owner],
                main_language_project=None,
            )
            self.pip.add_subproject(self.subproject, alias='sub')
            self.pip.translations.add(self.translation)


@override_settings(PUBLIC_DOMAIN='readthedocs.org')
class ResolverDomainTestsAlt(ResolverAltSetUp, ResolverDomainTests):
    pass


@override_settings(PUBLIC_DOMAIN='readthedocs.org')
class SmartResolverPathTestsAlt(ResolverAltSetUp, SmartResolverPathTests):
    pass


@override_settings(PUBLIC_DOMAIN='readthedocs.org')
class ResolverTestsAlt(ResolverAltSetUp, ResolverTests):
    pass


@override_settings(USE_SUBDOMAIN=True, PUBLIC_DOMAIN='readthedocs.io')
class TestSubprojectsWithTranslations(TestCase):

    def setUp(self):
        self.subproject_en = fixture.get(
            Project,
            language='en',
            privacy_level='public',
            main_language_project=None,
        )
        self.subproject_es = fixture.get(
            Project,
            language='es',
            privacy_level='public',
            main_language_project=self.subproject_en,
        )
        self.superproject_en = fixture.get(
            Project,
            language='en',
            privacy_level='public',
            main_language_project=None,
        )
        self.superproject_es = fixture.get(
            Project,
            language='es',
            privacy_level='public',
            main_language_project=self.superproject_en,
        )
        self.relation = fixture.get(
            ProjectRelationship,
            parent=self.superproject_en,
            child=self.subproject_en,
            alias=None,
        )
        self.assertIn(self.relation, self.superproject_en.subprojects.all())
        self.assertEqual(self.superproject_en.subprojects.count(), 1)

    def test_subproject_with_translation_without_custom_domain(self):
        url = resolve(self.superproject_en, filename='')
        self.assertEqual(
            url, 'http://{project.slug}.readthedocs.io/en/latest/'.format(
                project=self.superproject_en,
            ),
        )

        url = resolve(self.superproject_es, filename='')
        self.assertEqual(
            url, 'http://{project.slug}.readthedocs.io/es/latest/'.format(
                project=self.superproject_en,
            ),
        )

        url = resolve(self.subproject_en, filename='')
        # yapf: disable
        self.assertEqual(
            url,
            (
                'http://{project.slug}.readthedocs.io/projects/'
                '{subproject.slug}/en/latest/'
            ).format(
                project=self.superproject_en,
                subproject=self.subproject_en,
            ),
        )

        url = resolve(self.subproject_es, filename='')
        self.assertEqual(
            url,
            (
                'http://{project.slug}.readthedocs.io/projects/'
                '{subproject.slug}/es/latest/'
            ).format(
                project=self.superproject_en,
                subproject=self.subproject_en,
            ),
        )
        # yapf: enable

    def test_subproject_with_translation_with_custom_domain(self):
        fixture.get(
            Domain,
            domain='docs.example.com',
            canonical=True,
            cname=True,
            https=False,
            project=self.superproject_en,
        )

        url = resolve(self.superproject_en, filename='')
        self.assertEqual(url, 'http://docs.example.com/en/latest/')

        url = resolve(self.superproject_es, filename='')
        self.assertEqual(url, 'http://docs.example.com/es/latest/')

        # yapf: disable
        url = resolve(self.subproject_en, filename='')
        self.assertEqual(
            url,
            (
                'http://docs.example.com/projects/'
                '{subproject.slug}/en/latest/'
            ).format(
                subproject=self.subproject_en,
            ),
        )

        url = resolve(self.subproject_es, filename='')
        self.assertEqual(
            url,
            (
                'http://docs.example.com/projects/'
                '{subproject.slug}/es/latest/'
            ).format(
                subproject=self.subproject_en,
            ),
        )
        # yapf: enable
