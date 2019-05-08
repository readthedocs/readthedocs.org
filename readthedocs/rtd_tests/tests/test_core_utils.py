"""Test core util functions."""

import os

import mock
from django.http import Http404
from django.test import TestCase
from django_dynamic_fixture import get
from mock import call

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.core.utils import slugify, trigger_build
from readthedocs.core.utils.general import wipe_version_via_slugs
from readthedocs.projects.models import Project
from readthedocs.projects.tasks import remove_dirs


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
            'version_pk': version_1.pk,
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
        }

        update_docs_task.signature.assert_has_calls([
            mock.call(
                args=(project_1.pk,),
                kwargs=kwargs,
                options=mock.ANY,
                immutable=True,
            ),
        ])

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    def test_trigger_build_when_version_not_provided_default_version_doesnt_exist(self, update_docs_task):

        trigger_build(project=self.project)
        default_version = self.project.get_default_version()
        version_ = self.project.versions.get(slug=default_version)

        self.assertEqual(version_.slug, LATEST)

        kwargs = {
            'version_pk': version_.pk,
            'record': True,
            'force': False,
            'build_pk': mock.ANY,
        }

        update_docs_task.signature.assert_has_calls([
            mock.call(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=mock.ANY,
                immutable=True,
            ),
        ])

    @mock.patch('readthedocs.projects.tasks.clean_build_task')
    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    @mock.patch('readthedocs.core.utils.chain')
    def test_trigger_custom_queue(self, chain, update_docs, clean_build_task):
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
        chain.assert_called_with(
            update_docs.signature(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=options,
                immutable=True,
            ),
            clean_build_task.signature(
                args=(self.version.pk,),
                immutable=True,
            ),
        )

    @mock.patch('readthedocs.projects.tasks.clean_build_task')
    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    @mock.patch('readthedocs.core.utils.chain')
    def test_trigger_build_time_limit(self, chain, update_docs, clean_build_task):
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
        chain.assert_called_with(
            update_docs.signature(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=options,
                immutable=True,
            ),
            clean_build_task.signature(
                args=(self.version.pk,),
                immutable=True,
            ),
        )

    @mock.patch('readthedocs.projects.tasks.clean_build_task')
    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    @mock.patch('readthedocs.core.utils.chain')
    def test_trigger_build_invalid_time_limit(self, chain, update_docs, clean_build_task):
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
        chain.assert_called_with(
            update_docs.signature(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=options,
                immutable=True,
            ),
            clean_build_task.signature(
                args=(self.version.pk,),
                immutable=True,
            ),
        )

    @mock.patch('readthedocs.projects.tasks.clean_build_task')
    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    @mock.patch('readthedocs.core.utils.chain')
    def test_trigger_build_rounded_time_limit(self, chain, update_docs, clean_build_task):
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
        chain.assert_called_with(
            update_docs.signature(
                args=(self.project.pk,),
                kwargs=kwargs,
                options=options,
                immutable=True,
            ),
            clean_build_task.signature(
                args=(self.version.pk,),
                immutable=True,
            ),
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
