from django.test import override_settings
import django_dynamic_fixture as fixture
import pytest

from readthedocs.rtd_tests.tests.test_resolver import ResolverBase
from readthedocs.core.unresolver import unresolve
from readthedocs.projects.models import Domain


@override_settings(
    PUBLIC_DOMAIN='readthedocs.io',
    RTD_EXTERNAL_VERSION_DOMAIN='dev.readthedocs.build',
)
@pytest.mark.proxito
class UnResolverTests(ResolverBase):

    def test_unresolver(self):
        parts = unresolve('http://pip.readthedocs.io/en/latest/foo.html#fragment')
        self.assertEqual(parts.project.slug, 'pip')
        self.assertEqual(parts.language_slug, 'en')
        self.assertEqual(parts.version_slug, 'latest')
        self.assertEqual(parts.filename, 'foo.html')
        self.assertEqual(parts.fragment, 'fragment')

    def test_unresolver_subproject(self):
        parts = unresolve('http://pip.readthedocs.io/projects/sub/ja/latest/foo.html')
        self.assertEqual(parts.project.slug, 'sub')
        self.assertEqual(parts.language_slug, 'ja')
        self.assertEqual(parts.version_slug, 'latest')
        self.assertEqual(parts.filename, 'foo.html')

    def test_unresolver_translation(self):
        parts = unresolve('http://pip.readthedocs.io/ja/latest/foo.html')
        self.assertEqual(parts.project.slug, 'trans')
        self.assertEqual(parts.language_slug, 'ja')
        self.assertEqual(parts.version_slug, 'latest')
        self.assertEqual(parts.filename, 'foo.html')

    def test_unresolver_domain(self):
        self.domain = fixture.get(
            Domain,
            domain='docs.foobar.com',
            project=self.pip,
            canonical=True,
        )
        parts = unresolve('http://docs.foobar.com/en/latest/')
        self.assertEqual(parts.project.slug, 'pip')
        self.assertEqual(parts.language_slug, 'en')
        self.assertEqual(parts.version_slug, 'latest')
        self.assertEqual(parts.filename, 'index.html')

    def test_unresolver_single_version(self):
        self.pip.single_version = True
        parts = unresolve('http://pip.readthedocs.io/')
        self.assertEqual(parts.project.slug, 'pip')
        self.assertEqual(parts.language_slug, None)
        self.assertEqual(parts.version_slug, None)
        self.assertEqual(parts.filename, 'index.html')

    def test_unresolver_subproject_alias(self):
        relation = self.pip.subprojects.first()
        relation.alias = 'sub_alias'
        relation.save()
        parts = unresolve('http://pip.readthedocs.io/projects/sub_alias/ja/latest/')
        self.assertEqual(parts.project.slug, 'sub')
        self.assertEqual(parts.language_slug, 'ja')
        self.assertEqual(parts.version_slug, 'latest')
        self.assertEqual(parts.filename, 'index.html')

    def test_unresolver_external_version(self):
        ver = self.pip.versions.first()
        ver.type = 'external'
        ver.slug = '10'
        parts = unresolve('http://pip--10.dev.readthedocs.build/en/10/')
        self.assertEqual(parts.project.slug, 'pip')
        self.assertEqual(parts.language_slug, 'en')
        self.assertEqual(parts.version_slug, '10')
        self.assertEqual(parts.filename, 'index.html')

    def test_unresolver_unknown_host(self):
        parts = unresolve('http://random.stuff.com/en/latest/')
        self.assertEqual(parts, None)
