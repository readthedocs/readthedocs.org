from __future__ import division, print_function, unicode_literals

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project


class VersionConfigTests(TestCase):

    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)

    def test_get_correct_config(self):
        build_old = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 1}
        )
        build_new = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 2}
        )
        build_new_error = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 3},
            success=False,
        )
        build_new_unfinish = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 4},
            state='building',
        )
        config = self.version.config
        self.assertEqual(config, {'version': 2})
