from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.forms import VersionForm
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import Project


class TestVersionForm(TestCase):

    def setUp(self):
        self.project = get(Project)

    def test_default_version_is_active(self):
        version = get(
            Version,
            project=self.project,
            active=False,
        )
        self.project.default_version = version.slug
        self.project.save()

        form = VersionForm(
            {
                'slug': version.slug,
                'active': True,
                'privacy_level': PRIVATE,
            },
            instance=version,
        )
        self.assertTrue(form.is_valid())

    def test_default_version_is_inactive(self):
        version = get(
            Version,
            project=self.project,
            active=True,
        )
        self.project.default_version = version.slug
        self.project.save()

        form = VersionForm(
            {
                'slug': version.slug,
                'active': False,
                'privacy_level': PRIVATE,
            },
            instance=version,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('active', form.errors)

    def test_change_slug(self):
        version = get(
            Version,
            project=self.project,
            active=True,
            slug='slug',
        )

        test_slugs = (
            ('anotherslug', 'anotherslug'),
            ('another_slug', 'another_slug'),
            ('Another/Slug', 'another-slug'),
        )
        for slug, expected in test_slugs:
            form = VersionForm(
                {
                    'slug': slug,
                    'active': True,
                    'privacy_level': PUBLIC,
                },
                instance=version,
            )
            self.assertTrue(form.is_valid())
            self.assertEqual(version.slug, expected)

    def test_change_slug_wrong_valud(self):
        version = get(
            Version,
            project=self.project,
            active=True,
            slug='slug',
        )

        test_slugs = (
            '',
            '???//',
            'long' * 100,
        )
        for slug in test_slugs:
            form = VersionForm(
                {
                    'slug': slug,
                    'active': True,
                    'privacy_level': PUBLIC,
                },
                instance=version,
            )
            self.assertFalse(form.is_valid())
            self.assertIn('slug', form.errors)

    def test_change_slug_already_in_use(self):
        version_one = get(
            Version,
            project=self.project,
            active=True,
            slug='one',
        )
        version_two = get(
            Version,
            project=self.project,
            active=True,
            slug='two',
        )

        form = VersionForm(
            {
                'slug': 'two',
                'active': True,
                'privacy_level': PUBLIC,
            },
            instance=version_one,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('slug', form.errors)


    def test_cant_change_slug_machine_created_versions(self):
        version = get(
            Version,
            project=self.project,
            slug='machine',
            active=True,
            machine=True,
        )
        latest_version = self.project.versions.get(
            slug='latest',
        )

        # Form works
        form = VersionForm(
            {
                'slug': 'latest',
                'active': False,
                'privacy_level': PUBLIC,
            },
            instance=version,
        )
        self.assertTrue(form.is_valid())


        # Can't change for machine created versions
        form = VersionForm(
            {
                'slug': 'change',
                'active': False,
                'privacy_level': PUBLIC,
            },
            instance=version,
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(version.slug, 'machine')

        # Can't change for latest
        form = VersionForm(
            {
                'slug': 'change',
                'active': True,
                'privacy_level': PUBLIC,
            },
            instance=latest_version,
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(latest_version.slug, 'latest')
