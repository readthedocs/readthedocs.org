from django.test import TestCase

from builds.models import Version
from builds.version_slug import VersionSlugField
from projects.models import Project


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

    def test_single_letter(self):
        version = Version.objects.create(
            verbose_name='v',
            project=self.pip)
        self.assertEqual(version.slug, 'v')

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
