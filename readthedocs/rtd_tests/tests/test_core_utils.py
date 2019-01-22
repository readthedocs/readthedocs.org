# -*- coding: utf-8 -*-
"""Test core util functions."""

import mock
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.core.utils import slugify, trigger_build
from readthedocs.projects.models import Project


class CoreUtilTests(TestCase):

    def setUp(self):
        self.project = get(Project, container_time_limit=None)
        self.version = get(Version, project=self.project)

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    def test_trigger_skipped_project(self, update_docs_task):
        self.project.skip = True
        self.project.save()
        result = trigger_build(
            project=self.project,
            version=self.version,
        )
        self.assertEqual(result, (None, None))
        self.assertFalse(update_docs_task.signature.called)
        self.assertFalse(update_docs_task.signature().apply_async.called)

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    def test_trigger_custom_queue(self, update_docs):
        """Use a custom queue when routing the task."""
        self.project.build_queue = 'build03'
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'version_pk': self.version.pk,
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
        }
        options = {
            'queue': 'build03',
            'time_limit': 720,
            'soft_time_limit': 600,
        }
        update_docs.signature.assert_has_calls([
            mock.call(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=options,
                immutable=True,
            ),
        ])
        update_docs.signature().apply_async.assert_called()

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    def test_trigger_build_time_limit(self, update_docs):
        """Pass of time limit."""
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'version_pk': self.version.pk,
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
        }
        options = {
            'queue': mock.ANY,
            'time_limit': 720,
            'soft_time_limit': 600,
        }
        update_docs.signature.assert_has_calls([
            mock.call(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=options,
                immutable=True,
            ),
        ])
        update_docs.signature().apply_async.assert_called()

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    def test_trigger_build_invalid_time_limit(self, update_docs):
        """Time limit as string."""
        self.project.container_time_limit = '200s'
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'version_pk': self.version.pk,
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
        }
        options = {
            'queue': mock.ANY,
            'time_limit': 720,
            'soft_time_limit': 600,
        }
        update_docs.signature.assert_has_calls([
            mock.call(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=options,
                immutable=True,
            ),
        ])
        update_docs.signature().apply_async.assert_called()

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    def test_trigger_build_rounded_time_limit(self, update_docs):
        """Time limit should round down."""
        self.project.container_time_limit = 3
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'version_pk': self.version.pk,
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
        }
        options = {
            'queue': mock.ANY,
            'time_limit': 3,
            'soft_time_limit': 3,
        }
        update_docs.signature.assert_has_calls([
            mock.call(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=options,
                immutable=True,
            ),
        ])
        update_docs.signature().apply_async.assert_called()

    def test_slugify(self):
        """Test additional slugify."""
        self.assertEqual(
            slugify('This is a test'),
            'this-is-a-test',
        )
        self.assertEqual(
            slugify('project_with_underscores-v.1.0'),
            'project-with-underscores-v10',
        )
        self.assertEqual(
            slugify('project_with_underscores-v.1.0', dns_safe=False),
            'project_with_underscores-v10',
        )
        self.assertEqual(
            slugify('A title_-_with separated parts'),
            'a-title-with-separated-parts',
        )
        self.assertEqual(
            slugify('A title_-_with separated parts', dns_safe=False),
            'a-title_-_with-separated-parts',
        )
