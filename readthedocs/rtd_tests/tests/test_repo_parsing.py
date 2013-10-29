import json

from django.test import TestCase

from builds.models import Version
from projects.models import Project


class TestRepoParsing(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.version = Version.objects.create(project=self.pip, identifier='latest',
                               verbose_name='latest', slug='latest',
                               active=True)

    def test_github(self):
        self.pip.repo = 'https://github.com/user/repo'
        self.assertEqual(self.version.get_github_url('file'), 'https://github.com/user/repo/blob/master/docs/file.rst')

        self.pip.repo = 'https://github.com/user/repo/'
        self.assertEqual(self.version.get_github_url('file'), 'https://github.com/user/repo/blob/master/docs/file.rst')

        self.pip.repo = 'https://github.com/user/repo.git'
        self.assertEqual(self.version.get_github_url('file'), 'https://github.com/user/repo/blob/master/docs/file.rst')

    def test_bitbucket(self):
        self.pip.repo = 'https://bitbucket.org/user/repo'
        self.assertEqual(self.version.get_bitbucket_url('file'), 'https://bitbucket.org/user/repo/src/master/docs/file.rst')

        self.pip.repo = 'https://bitbucket.org/user/repo/'
        self.assertEqual(self.version.get_bitbucket_url('file'), 'https://bitbucket.org/user/repo/src/master/docs/file.rst')

        self.pip.repo = 'https://bitbucket.org/user/repo.git'
        self.assertEqual(self.version.get_bitbucket_url('file'), 'https://bitbucket.org/user/repo/src/master/docs/file.rst')

