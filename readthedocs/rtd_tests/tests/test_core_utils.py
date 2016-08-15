"""Test core util functions"""

import mock

from django_dynamic_fixture import get
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.models import Project
from readthedocs.builds.models import Version
from readthedocs.core.utils import trigger_build


class CoreUtilTests(TestCase):

    def setUp(self):
        self.project = get(Project, container_time_limit=None)
        self.version = get(Version, project=self.project)

    @mock.patch('readthedocs.projects.tasks.update_docs')
    def test_trigger_build_time_limit(self, update_docs):
        """Pass of time limit"""
        trigger_build(project=self.project, version=self.version)
        update_docs.assert_has_calls([
            mock.call.apply_async(
                time_limit=720,
                soft_time_limit=600,
                queue=mock.ANY,
                kwargs={
                    'pk': self.project.id,
                    'force': False,
                    'basic': False,
                    'record': True,
                    'build_pk': mock.ANY,
                    'version_pk': self.version.id
                }
            )
        ])

    @mock.patch('readthedocs.projects.tasks.update_docs')
    def test_trigger_build_invalid_time_limit(self, update_docs):
        """Time limit as string"""
        self.project.container_time_limit = '200s'
        trigger_build(project=self.project, version=self.version)
        update_docs.assert_has_calls([
            mock.call.apply_async(
                time_limit=720,
                soft_time_limit=600,
                queue=mock.ANY,
                kwargs={
                    'pk': self.project.id,
                    'force': False,
                    'basic': False,
                    'record': True,
                    'build_pk': mock.ANY,
                    'version_pk': self.version.id
                }
            )
        ])

    @mock.patch('readthedocs.projects.tasks.update_docs')
    def test_trigger_build_rounded_time_limit(self, update_docs):
        """Time limit should round down"""
        self.project.container_time_limit = 3
        trigger_build(project=self.project, version=self.version)
        update_docs.assert_has_calls([
            mock.call.apply_async(
                time_limit=3,
                soft_time_limit=3,
                queue=mock.ANY,
                kwargs={
                    'pk': self.project.id,
                    'force': False,
                    'basic': False,
                    'record': True,
                    'build_pk': mock.ANY,
                    'version_pk': self.version.id
                }
            )
        ])
