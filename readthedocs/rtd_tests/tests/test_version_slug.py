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
        self.assertEqual(version.slug, 'releases__1.0')

    def test_uniqueness(self):
        Version.objects.create(
            verbose_name='1-0',
            project=self.pip)
        version = Version.objects.create(
            verbose_name='1%0',
            project=self.pip)
        self.assertEqual(version.slug, '1-0_a')

    def test_uniquifying_suffix(self):
        field = VersionSlugField(populate_from='foo')
        self.assertEqual(field.uniquifying_suffix(0), '_a')
        self.assertEqual(field.uniquifying_suffix(25), '_z')
        self.assertEqual(field.uniquifying_suffix(26), '_ba')
        self.assertEqual(field.uniquifying_suffix(52), '_ca')
