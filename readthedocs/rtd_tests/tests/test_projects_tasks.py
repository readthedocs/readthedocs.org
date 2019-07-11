from __future__ import division, print_function, unicode_literals

from django.test import TestCase
from django_dynamic_fixture import get
from mock import patch

from readthedocs.builds.constants import EXTERNAL, BUILD_STATUS_SUCCESS
from readthedocs.builds.models import Version, Build
from readthedocs.projects.models import Project
from readthedocs.projects.tasks import (
    sync_files,
    send_external_build_status,
)


class SyncFilesTests(TestCase):

    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_clean_old_artifacts(self, rmtree, copy):
        sync_files(self.project.pk, self.version.pk, 'sphinx',
                   html=True, delete_unsynced_media=True)
        pdf, epub, htmlzip = rmtree.call_args_list

        # pdf and epub are cleaned
        args, _ = pdf
        self.assertIn('pdf', args[0])
        args, _ = epub
        self.assertIn('epub', args[0])

        # Artifacts are copied to the rtd-builds directory
        assert rmtree.call_count == 3
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx', args[0])
        self.assertIn('rtd-builds', args[1])

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_pdf(self, rmtree, copy):
        sync_files(
            self.project.pk, self.version.pk, 'sphinx', pdf=True, delete_unsynced_media=True
        )
        epub, htmlzip = rmtree.call_args_list

        # epub is cleaned
        args, _ = epub
        self.assertIn('epub', args[0])
        args, _ = htmlzip
        self.assertIn('htmlzip', args[0])

        # Artifacts are copied to the media directory
        assert rmtree.call_count == 2
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx_pdf', args[0])
        self.assertIn('media/pdf', args[1])

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_epub(self, rmtree, copy):
        sync_files(
            self.project.pk, self.version.pk, 'sphinx', epub=True, delete_unsynced_media=True
        )

        pdf, htmlzip = rmtree.call_args_list

        # epub is cleaned
        args, _ = pdf
        self.assertIn('pdf', args[0])
        args, _ = htmlzip
        self.assertIn('htmlzip', args[0])

        # Artifacts are copied to the media directory
        assert rmtree.call_count == 2
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx_epub', args[0])
        self.assertIn('media/epub', args[1])

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_localmedia(self, rmtree, copy):
        sync_files(
            self.project.pk, self.version.pk, 'sphinx', localmedia=True, delete_unsynced_media=True
        )
        pdf, epub = rmtree.call_args_list

        # pdf and epub are cleaned
        args, _ = pdf
        self.assertIn('pdf', args[0])
        args, _ = epub
        self.assertIn('epub', args[0])

        # Artifacts are copied to the media directory
        assert rmtree.call_count == 2
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx_localmedia', args[0])
        self.assertIn('media/htmlzip', args[1])

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_search(self, rmtree, copy):
        sync_files(
            self.project.pk, self.version.pk, 'sphinx', search=True, delete_unsynced_media=True
        )
        pdf, epub, htmlzip = rmtree.call_args_list

        # pdf and epub are cleaned
        args, _ = pdf
        self.assertIn('pdf', args[0])
        args, _ = epub
        self.assertIn('epub', args[0])
        args, _ = htmlzip
        self.assertIn('htmlzip', args[0])

        # Artifacts are copied to the media directory
        copy.assert_called_once()
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx_search', args[0])
        self.assertIn('media/json', args[1])


class SendBuildStatusTests(TestCase):

    def setUp(self):
        self.project = get(Project)
        self.internal_version = get(Version, project=self.project)
        self.external_version = get(Version, project=self.project, type=EXTERNAL)
        self.external_build = get(Build, project=self.project, version=self.external_version)
        self.internal_build = get(Build, project=self.project, version=self.internal_version)

    @patch('readthedocs.projects.tasks.send_build_status')
    def test_send_external_build_status_with_external_version(self, send_build_status):
        send_external_build_status(self.external_version,
                                   self.external_build.id, BUILD_STATUS_SUCCESS)

        send_build_status.delay.assert_called_once_with(self.external_build, BUILD_STATUS_SUCCESS)

    @patch('readthedocs.projects.tasks.send_build_status')
    def test_send_external_build_status_with_internal_version(self, send_build_status):
        send_external_build_status(self.internal_version,
                                   self.internal_build.id, BUILD_STATUS_SUCCESS)

        send_build_status.delay.assert_not_called()
