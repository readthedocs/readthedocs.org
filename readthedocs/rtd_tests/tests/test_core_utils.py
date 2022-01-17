"""Test core util functions."""

from unittest import mock

import pytest
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_BUILDING, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import slugify, trigger_build
from readthedocs.doc_builder.exceptions import BuildMaxConcurrencyError
from readthedocs.projects.constants import (
    CELERY_HIGH,
    CELERY_LOW,
    CELERY_MEDIUM,
)
from readthedocs.projects.models import Feature, Project


class CoreUtilTests(TestCase):

    def setUp(self):
        self.project = get(Project, container_time_limit=None, main_language_project=None)
        self.version = get(Version, project=self.project)

    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
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

    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_build_when_version_not_provided_default_version_exist(self, update_docs_task):
        self.assertFalse(Version.objects.filter(slug='test-default-version').exists())

        project_1 = get(Project)
        version_1 = get(Version, project=project_1, slug='test-default-version', active=True)

        project_1.default_version = 'test-default-version'
        project_1.save()

        default_version = project_1.get_default_version()
        self.assertEqual(default_version, 'test-default-version')

        trigger_build(project=project_1)
        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }

        update_docs_task.signature.assert_called_with(
            args=(version_1.pk,),
            kwargs=kwargs,
            options=mock.ANY,
            immutable=True,
        )

    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_build_when_version_not_provided_default_version_doesnt_exist(self, update_docs_task):

        trigger_build(project=self.project)
        default_version = self.project.get_default_version()
        version = self.project.versions.get(slug=default_version)

        self.assertEqual(version.slug, LATEST)

        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }

        update_docs_task.signature.assert_called_with(
            args=(version.pk,),
            kwargs=kwargs,
            options=mock.ANY,
            immutable=True,
        )

    @pytest.mark.xfail(reason='Fails while we work out Docker time limits', strict=True)
    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_custom_queue(self, update_docs):
        """Use a custom queue when routing the task."""
        self.project.build_queue = 'build03'
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }
        options = {
            'queue': 'build03',
            'time_limit': 720,
            'soft_time_limit': 600,
            'priority': CELERY_HIGH,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

    @pytest.mark.xfail(reason='Fails while we work out Docker time limits', strict=True)
    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_build_time_limit(self, update_docs):
        """Pass of time limit."""
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }
        options = {
            'queue': mock.ANY,
            'time_limit': 720,
            'soft_time_limit': 600,
            'priority': CELERY_HIGH,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

    @pytest.mark.xfail(reason='Fails while we work out Docker time limits', strict=True)
    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_build_invalid_time_limit(self, update_docs):
        """Time limit as string."""
        self.project.container_time_limit = '200s'
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }
        options = {
            'queue': mock.ANY,
            'time_limit': 720,
            'soft_time_limit': 600,
            'priority': CELERY_HIGH,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_build_rounded_time_limit(self, update_docs):
        """Time limit should round down."""
        self.project.container_time_limit = 3
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }
        options = {
            'time_limit': 3,
            'soft_time_limit': 3,
            'priority': CELERY_HIGH,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

    @pytest.mark.xfail(reason='Fails while we work out Docker time limits', strict=True)
    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_max_concurrency_reached(self, update_docs):
        get(
            Feature,
            feature_id=Feature.LIMIT_CONCURRENT_BUILDS,
            projects=[self.project],
        )
        max_concurrent_builds = 2
        for _ in range(max_concurrent_builds):
            get(
                Build,
                state=BUILD_STATE_BUILDING,
                project=self.project,
                version=self.version,
            )
        self.project.max_concurrent_builds = max_concurrent_builds
        self.project.save()

        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }
        options = {
            'queue': mock.ANY,
            'time_limit': 720,
            'soft_time_limit': 600,
            'countdown': 5 * 60,
            'max_retries': 25,
            'priority': CELERY_HIGH,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )
        build = self.project.builds.first()
        self.assertEqual(build.error, BuildMaxConcurrencyError.message.format(limit=max_concurrent_builds))

    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_external_build_low_priority(self, update_docs):
        """Time limit should round down."""
        self.version.type = 'external'
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }
        options = {
            'time_limit': mock.ANY,
            'soft_time_limit': mock.ANY,
            'priority': CELERY_LOW,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

    @mock.patch('readthedocs.projects.tasks.builds.update_docs_task')
    def test_trigger_build_translation_medium_priority(self, update_docs):
        """Time limit should round down."""
        self.project.main_language_project = get(Project, slug='main')
        trigger_build(project=self.project, version=self.version)
        kwargs = {
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
            'commit': None
        }
        options = {
            'time_limit': mock.ANY,
            'soft_time_limit': mock.ANY,
            'priority': CELERY_MEDIUM,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

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
            slugify('__project_with_trailing-underscores---'),
            'project-with-trailing-underscores',
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
