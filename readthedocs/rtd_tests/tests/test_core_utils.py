"""Test core util functions."""

import os

import pytest
from unittest import mock
from django.http import Http404
from django.test import TestCase
from django_dynamic_fixture import get
from unittest.mock import call

from readthedocs.builds.constants import LATEST, BUILD_STATE_BUILDING
from readthedocs.builds.models import Version, Build
from readthedocs.core.utils import slugify, trigger_build, prepare_build
from readthedocs.core.utils.general import wipe_version_via_slugs
from readthedocs.doc_builder.exceptions import BuildMaxConcurrencyError
from readthedocs.projects.constants import CELERY_LOW, CELERY_MEDIUM, CELERY_HIGH
from readthedocs.projects.models import Project, Feature
from readthedocs.projects.tasks import remove_dirs


class CoreUtilTests(TestCase):

    def setUp(self):
        self.project = get(Project, container_time_limit=None, main_language_project=None)
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

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
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
    @mock.patch('readthedocs.projects.tasks.update_docs_task')
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
    @mock.patch('readthedocs.projects.tasks.update_docs_task')
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
    @mock.patch('readthedocs.projects.tasks.update_docs_task')
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

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
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
    @mock.patch('readthedocs.projects.tasks.update_docs_task')
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

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
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

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
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

    @mock.patch('readthedocs.core.utils.general.broadcast')
    def test_wipe_version_via_slug(self, mock_broadcast):
        wipe_version_via_slugs(
            version_slug=self.version.slug,
            project_slug=self.version.project.slug
        )
        expected_del_dirs = [
            os.path.join(self.version.project.doc_path, 'checkouts', self.version.slug),
            os.path.join(self.version.project.doc_path, 'envs', self.version.slug),
            os.path.join(self.version.project.doc_path, 'conda', self.version.slug),
        ]

        mock_broadcast.assert_has_calls(
            [
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[0],)]),
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[1],)]),
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[2],)]),
            ],
            any_order=False
        )

    @mock.patch('readthedocs.core.utils.general.broadcast')
    def test_wipe_version_via_slug_wrong_param(self, mock_broadcast):
        self.assertFalse(Version.objects.filter(slug='wrong-slug').exists())
        with self.assertRaises(Http404):
            wipe_version_via_slugs(
                version_slug='wrong-slug',
                project_slug=self.version.project.slug
            )
        mock_broadcast.assert_not_called()

    @mock.patch('readthedocs.core.utils.general.broadcast')
    def test_wipe_version_via_slugs_same_version_slug_with_diff_proj(self, mock_broadcast):
        project_2 = get(Project)
        version_2 = get(Version, project=project_2, slug=self.version.slug)
        wipe_version_via_slugs(
            version_slug=version_2.slug,
            project_slug=project_2.slug,
        )

        expected_del_dirs = [
            os.path.join(version_2.project.doc_path, 'checkouts', version_2.slug),
            os.path.join(version_2.project.doc_path, 'envs', version_2.slug),
            os.path.join(version_2.project.doc_path, 'conda', version_2.slug),
        ]

        mock_broadcast.assert_has_calls(
            [
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[0],)]),
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[1],)]),
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[2],)]),
            ],
            any_order=False
        )
