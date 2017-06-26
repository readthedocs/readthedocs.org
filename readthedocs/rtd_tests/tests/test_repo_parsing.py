from __future__ import absolute_import
import json

from django.test import TestCase

from readthedocs.projects.models import Project


class TestRepoParsing(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.version = self.pip.versions.create_latest()

    def test_github(self):
        self.pip.repo = 'https://github.com/user/repo'
        self.assertEqual(self.version.get_github_url(docroot='/docs/', filename='file'), 'https://github.com/user/repo/blob/master/docs/file.rst')

        self.pip.repo = 'https://github.com/user/repo/'
        self.assertEqual(self.version.get_github_url(docroot='/docs/', filename='file'), 'https://github.com/user/repo/blob/master/docs/file.rst')

        self.pip.repo = 'https://github.com/user/repo.git'
        self.assertEqual(self.version.get_github_url(docroot='/docs/', filename='file'), 'https://github.com/user/repo/blob/master/docs/file.rst')

    def test_bitbucket(self):
        self.pip.repo = 'https://bitbucket.org/user/repo'
        self.assertEqual(self.version.get_bitbucket_url(docroot='/foo/bar/', filename='file'), 'https://bitbucket.org/user/repo/src/master/foo/bar/file.rst')

        self.pip.repo = 'https://bitbucket.org/user/repo/'
        self.assertEqual(self.version.get_bitbucket_url(docroot='/foo/bar/', filename='file'), 'https://bitbucket.org/user/repo/src/master/foo/bar/file.rst')

        self.pip.repo = 'https://bitbucket.org/user/repo.git'
        self.assertEqual(self.version.get_bitbucket_url(docroot='/foo/bar/', filename='file'), 'https://bitbucket.org/user/repo/src/master/foo/bar/file.rst')

