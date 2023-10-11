import django_dynamic_fixture as fixture
import pytest
from django.test import TestCase, override_settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.resolver import Resolver, resolve, resolve_domain, resolve_path
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import Domain, Project, ProjectRelationship
from readthedocs.rtd_tests.utils import create_user
from readthedocs.subscriptions.constants import TYPE_CNAME
from readthedocs.subscriptions.products import RTDProductFeature


@override_settings(
    PUBLIC_DOMAIN="readthedocs.org",
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(type=TYPE_CNAME).to_item()]),
)
class ResolverBase(TestCase):
    def setUp(self):
        self.owner = create_user(username="owner", password="test")
        self.tester = create_user(username="tester", password="test")
        self.pip = fixture.get(
            Project,
            slug="pip",
            users=[self.owner],
            main_language_project=None,
        )
        self.version = self.pip.versions.first()
        self.subproject = fixture.get(
            Project,
            slug="sub",
            language="ja",
            users=[self.owner],
            main_language_project=None,
        )
        self.subproject_version = self.subproject.versions.first()
        self.translation = fixture.get(
            Project,
            slug="trans",
            language="ja",
            users=[self.owner],
            main_language_project=None,
        )
        self.translation_version = self.translation.versions.first()
        self.pip.add_subproject(self.subproject)
        self.pip.translations.add(self.translation)

        self.subproject_translation = fixture.get(
            Project,
            slug="subproject-translation",
            language="es",
            users=[self.owner],
        )
        self.subproject_translation_version = (
            self.subproject_translation.versions.first()
        )
        self.subproject.translations.add(self.subproject_translation)


class SmartResolverPathTests(ResolverBase):
    def test_resolver_filename(self):
        url = resolve_path(project=self.pip, filename="/foo/bar/blah.html")
        self.assertEqual(url, "/en/latest/foo/bar/blah.html")

        url = resolve_path(project=self.pip, filename="")
        self.assertEqual(url, "/en/latest/")

    def test_resolver_filename_index(self):
        url = resolve_path(project=self.pip, filename="foo/bar/index.html")
        self.assertEqual(url, "/en/latest/foo/bar/index.html")
        url = resolve_path(
            project=self.pip,
            filename="foo/index/index.html",
        )
        self.assertEqual(url, "/en/latest/foo/index/index.html")

    def test_resolver_filename_false_index(self):
        url = resolve_path(project=self.pip, filename="foo/foo_index.html")
        self.assertEqual(url, "/en/latest/foo/foo_index.html")
        url = resolve_path(
            project=self.pip,
            filename="foo_index/foo_index.html",
        )
        self.assertEqual(
            url,
            "/en/latest/foo_index/foo_index.html",
        )

    def test_resolver_filename_sphinx(self):
        self.pip.documentation_type = "sphinx"
        url = resolve_path(project=self.pip, filename="foo/bar")
        self.assertEqual(url, "/en/latest/foo/bar")

        url = resolve_path(project=self.pip, filename="foo/index")
        self.assertEqual(url, "/en/latest/foo/index")

    def test_resolver_filename_mkdocs(self):
        self.pip.documentation_type = "mkdocs"
        url = resolve_path(project=self.pip, filename="foo/bar")
        self.assertEqual(url, "/en/latest/foo/bar")

        url = resolve_path(project=self.pip, filename="foo/index.html")
        self.assertEqual(url, "/en/latest/foo/index.html")

        url = resolve_path(project=self.pip, filename="foo/bar.html")
        self.assertEqual(url, "/en/latest/foo/bar.html")

    def test_resolver_subdomain(self):
        url = resolve_path(project=self.pip, filename="index.html")
        self.assertEqual(url, "/en/latest/index.html")

    def test_resolver_domain_object(self):
        self.domain = fixture.get(
            Domain,
            domain="http://docs.foobar.com",
            project=self.pip,
            canonical=True,
            https=False,
        )
        url = resolve_path(project=self.pip, filename="index.html")
        self.assertEqual(url, "/en/latest/index.html")

    def test_resolver_domain_object_not_canonical(self):
        self.domain = fixture.get(
            Domain,
            domain="http://docs.foobar.com",
            project=self.pip,
            canonical=False,
            https=False,
        )
        url = resolve_path(project=self.pip, filename="")
        self.assertEqual(url, "/en/latest/")

    def test_resolver_subproject_subdomain(self):
        url = resolve_path(project=self.subproject, filename="index.html")
        self.assertEqual(url, "/projects/sub/ja/latest/index.html")

    def test_resolver_subproject_single_version(self):
        self.subproject.single_version = True
        url = resolve_path(project=self.subproject, filename="index.html")
        self.assertEqual(url, "/projects/sub/index.html")

    def test_resolver_subproject_both_single_version(self):
        self.pip.single_version = True
        self.subproject.single_version = True
        url = resolve_path(project=self.subproject, filename="index.html")
        self.assertEqual(url, "/projects/sub/index.html")

    def test_resolver_translation(self):
        url = resolve_path(project=self.translation, filename="index.html")
        self.assertEqual(url, "/ja/latest/index.html")


class ResolverPathOverrideTests(ResolverBase):

    """Tests to make sure we can override resolve_path correctly."""

    def test_resolver_force_single_version(self):
        self.pip.single_version = False
        url = resolve_path(
            project=self.pip,
            filename="index.html",
            single_version=True,
        )
        self.assertEqual(url, "/index.html")

    def test_resolver_force_language(self):
        url = resolve_path(
            project=self.pip,
            filename="index.html",
            language="cz",
        )
        self.assertEqual(url, "/cz/latest/index.html")

    def test_resolver_force_version(self):
        url = resolve_path(
            project=self.pip,
            filename="index.html",
            version_slug="foo",
        )
        self.assertEqual(url, "/en/foo/index.html")

    def test_resolver_force_language_version(self):
        url = resolve_path(
            project=self.pip,
            filename="index.html",
            language="cz",
            version_slug="foo",
        )
        self.assertEqual(url, "/cz/foo/index.html")


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
    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_domain_resolver(self):
        url = resolve_domain(project=self.pip)
        self.assertEqual(url, "pip.readthedocs.org")

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="readthedocs.io",
    )
    def test_domain_resolver_with_domain_object(self):
        self.domain = fixture.get(
            Domain,
            domain="docs.foobar.com",
            project=self.pip,
            canonical=True,
            https=False,
        )
        url = resolve_domain(project=self.pip)
        self.assertEqual(url, "docs.foobar.com")

        url = resolve_domain(project=self.pip, use_canonical_domain=False)
        self.assertEqual(url, "pip.readthedocs.io")

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="readthedocs.io",
    )
    def test_domain_resolver_subproject(self):
        url = resolve_domain(project=self.subproject)
        self.assertEqual(url, "pip.readthedocs.io")

        url = resolve_domain(project=self.subproject, use_canonical_domain=False)
        self.assertEqual(url, "pip.readthedocs.io")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
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

        url = resolve_domain(project=self.pip)
        self.assertEqual(url, "pip.readthedocs.org")

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="readthedocs.io",
    )
    def test_domain_resolver_translation(self):
        url = resolve_domain(project=self.translation)
        self.assertEqual(url, "pip.readthedocs.io")

        url = resolve_domain(project=self.translation, use_canonical_domain=False)
        self.assertEqual(url, "pip.readthedocs.io")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
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

        url = resolve_domain(project=self.pip)
        self.assertEqual(url, "pip.readthedocs.org")

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="public.readthedocs.org",
    )
    def test_domain_public(self):
        url = resolve_domain(project=self.translation)
        self.assertEqual(url, "pip.public.readthedocs.org")

        url = resolve_domain(project=self.translation, use_canonical_domain=False)
        self.assertEqual(url, "pip.public.readthedocs.org")

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="public.readthedocs.org",
        RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
        PUBLIC_DOMAIN_USES_HTTPS=True,
    )
    def test_domain_external(self):
        latest = self.pip.versions.first()
        latest.type = EXTERNAL
        latest.save()
        url = resolve(project=self.pip)
        self.assertEqual(url, "https://pip--latest.dev.readthedocs.build/en/latest/")
        url = resolve(project=self.pip, version_slug=latest.slug)
        self.assertEqual(url, "https://pip--latest.dev.readthedocs.build/en/latest/")
        url = resolve(project=self.pip, version_slug="non-external")
        self.assertEqual(url, "https://pip.public.readthedocs.org/en/non-external/")


class ResolverTests(ResolverBase):
    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver(self):
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://pip.readthedocs.org/en/latest/")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_domain(self):
        self.domain = fixture.get(
            Domain,
            domain="docs.foobar.com",
            project=self.pip,
            canonical=True,
            https=False,
        )
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://docs.foobar.com/en/latest/")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_domain_https(self):
        self.domain = fixture.get(
            Domain,
            domain="docs.foobar.com",
            project=self.pip,
            https=True,
            canonical=True,
        )
        url = resolve(project=self.pip)
        self.assertEqual(url, "https://docs.foobar.com/en/latest/")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_subproject(self):
        url = resolve(project=self.subproject)
        self.assertEqual(
            url,
            "http://pip.readthedocs.org/projects/sub/ja/latest/",
        )

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_translation(self):
        url = resolve(project=self.translation)
        self.assertEqual(url, "http://pip.readthedocs.org/ja/latest/")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_nested_translation_of_a_subproject(self):
        """The project is a translation, and the main translation is a subproject of a project."""
        translation = fixture.get(
            Project,
            slug="api-es",
            language="es",
            users=[self.owner],
            main_language_project=self.subproject,
        )

        url = resolve(project=translation)
        self.assertEqual(
            url,
            "http://pip.readthedocs.org/projects/sub/es/latest/",
        )

    @pytest.mark.xfail(reason="We do not support this for now", strict=True)
    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_nested_subproject_of_a_translation(self):
        """The project is a subproject, and the superproject is a translation of a project."""
        project = fixture.get(
            Project,
            slug="all-docs",
            language="en",
            users=[self.owner],
            main_language_project=None,
        )
        translation = fixture.get(
            Project,
            slug="docs-es",
            language="es",
            users=[self.owner],
            main_language_project=project,
        )

        subproject = fixture.get(
            Project,
            slug="api-es",
            language="es",
            users=[self.owner],
            main_language_project=None,
        )
        translation.add_subproject(subproject)

        url = resolve(project=subproject)
        self.assertEqual(
            url, "http://docs-es.readthedocs.org/projects/api-es/es/latest/"
        )

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_single_version(self):
        self.pip.single_version = True
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://pip.readthedocs.org/")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_subproject_alias(self):
        relation = self.pip.subprojects.first()
        relation.alias = "sub_alias"
        relation.save()
        url = resolve(project=self.subproject)
        self.assertEqual(
            url,
            "http://pip.readthedocs.org/projects/sub_alias/ja/latest/",
        )

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_private_project(self):
        self.pip.privacy_level = PRIVATE
        self.pip.save()
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://pip.readthedocs.org/en/latest/")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_private_project_override(self):
        self.pip.privacy_level = PRIVATE
        self.pip.save()
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://pip.readthedocs.org/en/latest/")
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://pip.readthedocs.org/en/latest/")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_resolver_private_version_override(self):
        latest = self.pip.versions.first()
        latest.privacy_level = PRIVATE
        latest.save()
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://pip.readthedocs.org/en/latest/")
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://pip.readthedocs.org/en/latest/")

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="public.readthedocs.org",
    )
    def test_resolver_public_domain_overrides(self):
        url = resolve(project=self.pip)
        self.assertEqual(
            url,
            "http://pip.public.readthedocs.org/en/latest/",
        )
        url = resolve(project=self.pip)
        self.assertEqual(
            url,
            "http://pip.public.readthedocs.org/en/latest/",
        )

        # Domain overrides PUBLIC_DOMAIN
        self.domain = fixture.get(
            Domain,
            domain="docs.foobar.com",
            project=self.pip,
            canonical=True,
            https=False,
        )
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://docs.foobar.com/en/latest/")
        url = resolve(project=self.pip)
        self.assertEqual(url, "http://docs.foobar.com/en/latest/")

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="readthedocs.io",
    )
    def test_resolver_domain_https(self):
        with override_settings(PUBLIC_DOMAIN_USES_HTTPS=True):
            url = resolve(project=self.pip)
            self.assertEqual(url, "https://pip.readthedocs.io/en/latest/")

            url = resolve(project=self.pip)
            self.assertEqual(url, "https://pip.readthedocs.io/en/latest/")

        with override_settings(PUBLIC_DOMAIN_USES_HTTPS=False):
            url = resolve(project=self.pip)
            self.assertEqual(url, "http://pip.readthedocs.io/en/latest/")


class ResolverAltSetUp:
    def setUp(self):
        self.owner = create_user(username="owner", password="test")
        self.tester = create_user(username="tester", password="test")
        self.pip = fixture.get(
            Project,
            slug="pip",
            users=[self.owner],
            main_language_project=None,
        )
        self.seed = fixture.get(
            Project,
            slug="sub",
            users=[self.owner],
            main_language_project=None,
        )
        self.subproject = fixture.get(
            Project,
            slug="subproject",
            language="ja",
            users=[self.owner],
            main_language_project=None,
        )
        self.translation = fixture.get(
            Project,
            slug="trans",
            language="ja",
            users=[self.owner],
            main_language_project=None,
        )
        self.pip.add_subproject(self.subproject, alias="sub")
        self.pip.translations.add(self.translation)


@override_settings(PUBLIC_DOMAIN="readthedocs.org")
class ResolverDomainTestsAlt(ResolverAltSetUp, ResolverDomainTests):
    pass


@override_settings(PUBLIC_DOMAIN="readthedocs.org")
class SmartResolverPathTestsAlt(ResolverAltSetUp, SmartResolverPathTests):
    pass


@override_settings(PUBLIC_DOMAIN="readthedocs.org")
class ResolverTestsAlt(ResolverAltSetUp, ResolverTests):
    pass


@override_settings(PUBLIC_DOMAIN="readthedocs.io")
class TestSubprojectsWithTranslations(TestCase):
    def setUp(self):
        self.subproject_en = fixture.get(
            Project,
            language="en",
            privacy_level="public",
            main_language_project=None,
        )
        self.subproject_es = fixture.get(
            Project,
            language="es",
            privacy_level="public",
            main_language_project=self.subproject_en,
        )
        self.superproject_en = fixture.get(
            Project,
            language="en",
            privacy_level="public",
            main_language_project=None,
        )
        self.superproject_es = fixture.get(
            Project,
            language="es",
            privacy_level="public",
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
        url = resolve(self.superproject_en, filename="")
        self.assertEqual(
            url,
            "http://{project.slug}.readthedocs.io/en/latest/".format(
                project=self.superproject_en,
            ),
        )

        url = resolve(self.superproject_es, filename="")
        self.assertEqual(
            url,
            "http://{project.slug}.readthedocs.io/es/latest/".format(
                project=self.superproject_en,
            ),
        )

        url = resolve(self.subproject_en, filename="")
        self.assertEqual(
            url,
            (
                "http://{project.slug}.readthedocs.io/projects/"
                "{subproject.slug}/en/latest/"
            ).format(
                project=self.superproject_en,
                subproject=self.subproject_en,
            ),
        )

        url = resolve(self.subproject_es, filename="")
        self.assertEqual(
            url,
            (
                "http://{project.slug}.readthedocs.io/projects/"
                "{subproject.slug}/es/latest/"
            ).format(
                project=self.superproject_en,
                subproject=self.subproject_en,
            ),
        )

    @override_settings(
        RTD_DEFAULT_FEATURES=dict([RTDProductFeature(TYPE_CNAME).to_item()]),
    )
    def test_subproject_with_translation_with_custom_domain(self):
        fixture.get(
            Domain,
            domain="docs.example.com",
            canonical=True,
            cname=True,
            https=False,
            project=self.superproject_en,
        )

        url = resolve(self.superproject_en, filename="")
        self.assertEqual(url, "http://docs.example.com/en/latest/")

        url = resolve(self.superproject_es, filename="")
        self.assertEqual(url, "http://docs.example.com/es/latest/")

        url = resolve(self.subproject_en, filename="")
        self.assertEqual(
            url,
            ("http://docs.example.com/projects/" "{subproject.slug}/en/latest/").format(
                subproject=self.subproject_en,
            ),
        )

        url = resolve(self.subproject_es, filename="")
        self.assertEqual(
            url,
            ("http://docs.example.com/projects/" "{subproject.slug}/es/latest/").format(
                subproject=self.subproject_en,
            ),
        )


@override_settings(
    PUBLIC_DOMAIN="readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="readthedocs.build",
)
class TestResolverWithCustomPrefixes(ResolverBase):
    def test_custom_prefix_multi_version_project(self):
        self.pip.custom_prefix = "/custom/prefix/"
        self.pip.save()

        url = resolve(self.pip)
        self.assertEqual(url, "http://pip.readthedocs.io/custom/prefix/en/latest/")

        url = resolve(self.pip, version_slug=self.version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/custom/prefix/en/latest/")

        url = resolve(self.pip, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/custom/prefix/en/stable/")

        url = resolve(
            self.pip, version_slug=self.version.slug, filename="/api/index.html"
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/custom/prefix/en/latest/api/index.html"
        )

    def test_custom_prefix_multi_version_project_translation(self):
        self.pip.custom_prefix = "/custom/prefix/"
        self.pip.save()

        url = resolve(self.translation)
        self.assertEqual(url, "http://pip.readthedocs.io/custom/prefix/ja/latest/")

        url = resolve(self.translation, version_slug=self.translation_version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/custom/prefix/ja/latest/")

        url = resolve(self.translation, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/custom/prefix/ja/stable/")

        url = resolve(
            self.translation,
            version_slug=self.translation_version.slug,
            filename="/api/index.html",
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/custom/prefix/ja/latest/api/index.html"
        )

    def test_custom_prefix_single_version_project(self):
        self.pip.single_version = True
        self.pip.custom_prefix = "/custom-prefix/"
        self.pip.save()

        url = resolve(self.pip)
        self.assertEqual(url, "http://pip.readthedocs.io/custom-prefix/")

        url = resolve(self.pip, version_slug=self.version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/custom-prefix/")

        url = resolve(self.pip, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/custom-prefix/")

        url = resolve(
            self.pip, version_slug=self.version.slug, filename="/api/index.html"
        )
        self.assertEqual(url, "http://pip.readthedocs.io/custom-prefix/api/index.html")

    def test_custom_subproject_prefix(self):
        self.pip.custom_subproject_prefix = "/custom/"
        self.pip.save()

        url = resolve(self.subproject)
        self.assertEqual(url, "http://pip.readthedocs.io/custom/sub/ja/latest/")

        url = resolve(self.subproject, version_slug=self.subproject_version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/custom/sub/ja/latest/")

        url = resolve(self.subproject, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/custom/sub/ja/stable/")

        url = resolve(
            self.subproject,
            version_slug=self.subproject_version.slug,
            filename="/api/index.html",
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/custom/sub/ja/latest/api/index.html"
        )

    def test_custom_subproject_prefix_empty(self):
        self.pip.custom_subproject_prefix = "/"
        self.pip.save()

        url = resolve(self.subproject)
        self.assertEqual(url, "http://pip.readthedocs.io/sub/ja/latest/")

        url = resolve(self.subproject, version_slug=self.subproject_version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/sub/ja/latest/")

        url = resolve(self.subproject, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/sub/ja/stable/")

        url = resolve(
            self.subproject,
            version_slug=self.subproject_version.slug,
            filename="/api/index.html",
        )
        self.assertEqual(url, "http://pip.readthedocs.io/sub/ja/latest/api/index.html")

    def test_custom_prefix_and_custom_subproject_prefix_in_superproject(self):
        self.pip.custom_prefix = "/prefix/"
        self.pip.custom_subproject_prefix = "/s/"
        self.pip.save()

        url = resolve(self.pip)
        self.assertEqual(url, "http://pip.readthedocs.io/prefix/en/latest/")

        url = resolve(self.pip, version_slug=self.version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/prefix/en/latest/")

        url = resolve(self.pip, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/prefix/en/stable/")

        url = resolve(
            self.pip, version_slug=self.version.slug, filename="/api/index.html"
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/prefix/en/latest/api/index.html"
        )

        url = resolve(self.subproject)
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/ja/latest/")

        url = resolve(self.subproject, version_slug=self.subproject_version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/ja/latest/")

        url = resolve(self.subproject, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/ja/stable/")

        url = resolve(
            self.subproject,
            version_slug=self.subproject_version.slug,
            filename="/api/index.html",
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/s/sub/ja/latest/api/index.html"
        )

    def test_custom_prefix_and_custom_subproject_prefix_with_translations(self):
        self.pip.custom_prefix = "/prefix/"
        self.pip.custom_subproject_prefix = "/s/"
        self.pip.save()

        url = resolve(self.translation)
        self.assertEqual(url, "http://pip.readthedocs.io/prefix/ja/latest/")

        url = resolve(self.translation, version_slug=self.translation_version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/prefix/ja/latest/")

        url = resolve(self.translation, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/prefix/ja/stable/")

        url = resolve(
            self.translation,
            version_slug=self.translation_version.slug,
            filename="/api/index.html",
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/prefix/ja/latest/api/index.html"
        )

        url = resolve(self.subproject_translation)
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/es/latest/")

        url = resolve(
            self.subproject_translation, version_slug=self.subproject_version.slug
        )
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/es/latest/")

        url = resolve(self.subproject_translation, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/es/stable/")

        url = resolve(
            self.subproject_translation,
            version_slug=self.subproject_version.slug,
            filename="/api/index.html",
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/s/sub/es/latest/api/index.html"
        )

    def test_custom_prefix_in_subproject_and_custom_prefix_in_superproject(self):
        self.subproject.custom_prefix = "/prefix/"
        self.subproject.save()
        self.pip.custom_subproject_prefix = "/s/"
        self.pip.save()

        url = resolve(self.subproject)
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/prefix/ja/latest/")

        url = resolve(self.subproject, version_slug=self.subproject_version.slug)
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/prefix/ja/latest/")

        url = resolve(self.subproject, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/prefix/ja/stable/")

        url = resolve(
            self.subproject,
            version_slug=self.subproject_version.slug,
            filename="/api/index.html",
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/s/sub/prefix/ja/latest/api/index.html"
        )

        url = resolve(self.subproject_translation)
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/prefix/es/latest/")

        url = resolve(
            self.subproject_translation, version_slug=self.subproject_version.slug
        )
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/prefix/es/latest/")

        url = resolve(self.subproject_translation, version_slug="stable")
        self.assertEqual(url, "http://pip.readthedocs.io/s/sub/prefix/es/stable/")

        url = resolve(
            self.subproject_translation,
            version_slug=self.subproject_version.slug,
            filename="/api/index.html",
        )
        self.assertEqual(
            url, "http://pip.readthedocs.io/s/sub/prefix/es/latest/api/index.html"
        )
