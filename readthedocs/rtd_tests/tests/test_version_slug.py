from __future__ import absolute_import
import re
from django.test import TestCase

from readthedocs.builds.models import Version
from readthedocs.builds.version_slug import VersionSlugField
from readthedocs.builds.version_slug import VERSION_SLUG_REGEX
from readthedocs.projects.models import Project


class VersionSlugPatternTests(TestCase):
    pattern = re.compile('^{pattern}$'.format(pattern=VERSION_SLUG_REGEX))

    def test_single_char(self):
        self.assertTrue(self.pattern.match('v'))
        self.assertFalse(self.pattern.match('.'))

    def test_trailing_punctuation(self):
        self.assertTrue(self.pattern.match('with_'))
        self.assertTrue(self.pattern.match('with.'))
        self.assertTrue(self.pattern.match('with-'))
        self.assertFalse(self.pattern.match('with!'))

    def test_multiple_words(self):
        self.assertTrue(self.pattern.match('release-1.0'))
        self.assertTrue(self.pattern.match('fix_this-and-that.'))


class VersionSlugFieldTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')

    def test_saving(self):
        version = Version.objects.create(
            verbose_name='1.0',
            project=self.pip)
        self.assertEqual(version.slug, '1.0')

    def test_normalizing(self):
        version = Version.objects.create(
            verbose_name='1%0',
            project=self.pip)
        self.assertEqual(version.slug, '1-0')

    def test_normalizing_slashes(self):
        version = Version.objects.create(
            verbose_name='releases/1.0',
            project=self.pip)
        self.assertEqual(version.slug, 'releases-1.0')

    def test_uppercase(self):
        version = Version.objects.create(
            verbose_name='SomeString-charclass',
            project=self.pip)
        self.assertEqual(version.slug, 'somestring-charclass')

    def test_placeholder_as_name(self):
        version = Version.objects.create(
            verbose_name='-',
            project=self.pip)
        self.assertEqual(version.slug, 'unknown')

    def test_multiple_empty_names(self):
        version = Version.objects.create(
            verbose_name='-',
            project=self.pip)
        self.assertEqual(version.slug, 'unknown')

        version = Version.objects.create(
            verbose_name='-./.-',
            project=self.pip)
        self.assertEqual(version.slug, 'unknown_a')

    def test_uniqueness(self):
        version = Version.objects.create(
            verbose_name='1!0',
            project=self.pip)
        self.assertEqual(version.slug, '1-0')

        version = Version.objects.create(
            verbose_name='1%0',
            project=self.pip)
        self.assertEqual(version.slug, '1-0_a')

        version = Version.objects.create(
            verbose_name='1?0',
            project=self.pip)
        self.assertEqual(version.slug, '1-0_b')

    def test_uniquifying_suffix(self):
        field = VersionSlugField(populate_from='foo')
        self.assertEqual(field.uniquifying_suffix(0), '_a')
        self.assertEqual(field.uniquifying_suffix(25), '_z')
        self.assertEqual(field.uniquifying_suffix(26), '_ba')
        self.assertEqual(field.uniquifying_suffix(52), '_ca')
