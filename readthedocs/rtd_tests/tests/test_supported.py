import json

from django.test import TestCase

from builds.models import Version
from projects.models import Project


class TestSupportedVersions(TestCase):

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.create(name='Pip', slug='pip')
        Version.objects.create(project=self.pip, identifier='latest',
                               verbose_name='latest', slug='latest',
                               type='branch',
                               active=True)
        Version.objects.create(project=self.pip, identifier='0.1',
                               verbose_name='0.1', slug='0.1',
                               type='tag',
                               active=True)
        Version.objects.create(project=self.pip, identifier='0.2',
                               verbose_name='0.2', slug='0.2',
                               type='tag',
                               active=True)

    """
    def test_supported_versions(self):
        self.pip.num_major = 1
        self.pip.num_minor = 1
        self.pip.num_point = 1
        self.assertEqual(self.pip.supported_versions(), [u'0.2'])

        self.pip.num_major = 1
        self.pip.num_minor = 2
        self.pip.num_point = 1
        self.assertEqual(self.pip.supported_versions(), [u'0.1', u'0.2'])

    def test_sync_supported_versions(self):
        self.assertEqual(self.pip.versions.get(slug='0.1').supported, True)
        self.assertEqual(self.pip.versions.get(slug='0.2').supported, True)
        self.pip.num_major = 1
        self.pip.num_minor = 1
        self.pip.num_point = 1
        self.pip.save()
        self.assertEqual(self.pip.versions.get(slug='0.1').supported, False)
        self.assertEqual(self.pip.versions.get(slug='0.2').supported, True)
        self.pip.num_major = 1
        self.pip.num_minor = 2
        self.pip.num_point = 1
        self.pip.save()
        self.assertEqual(self.pip.versions.get(slug='0.1').supported, True)
        self.assertEqual(self.pip.versions.get(slug='0.2').supported, True)

    def test_adding_version_updates_supported(self):
        self.pip.num_major = 1
        self.pip.num_minor = 1
        self.pip.num_point = 2
        self.pip.save()
        self.assertEqual(self.pip.versions.get(slug='0.1').supported, False)
        self.assertEqual(self.pip.versions.get(slug='0.2').supported, True)
        Version.objects.create(project=self.pip, identifier='0.1.1',
                               verbose_name='0.1.1', slug='0.1.1',
                               type='tag',
                               active=True)
        # This gets set to False on creation.
        self.assertEqual(self.pip.versions.get(slug='0.1.1').supported, False)
    """