from __future__ import division, print_function, unicode_literals

from django.test import TestCase
from django_dynamic_fixture import get
from mock import patch

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.tasks import sync_files


class SyncFilesTests(TestCase):

    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_clean_old_artifacts(self, rmtree, copy):
        sync_files(self.project.pk, self.version.pk, 'sphinx', html=True)
        pdf, epub = rmtree.call_args_list

        # pdf and epub are cleaned
        args, _ = pdf
        self.assertIn('pdf', args[0])
        args, _ = epub
        self.assertIn('epub', args[0])

        # Artifacts are copied to the rtd-builds directory
        copy.assert_called_once()
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx', args[0])
        self.assertIn('rtd-builds', args[1])

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_pdf(self, rmtree, copy):
        sync_files(
            self.project.pk, self.version.pk, 'sphinx', pdf=True
        )

        # epub is cleaned
        rmtree.assert_called_once()
        args, _ = rmtree.call_args
        self.assertIn('epub', args[0])

        # Artifacts are copied to the media directory
        copy.assert_called_once()
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx_pdf', args[0])
        self.assertIn('media/pdf', args[1])

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_epub(self, rmtree, copy):
        sync_files(
            self.project.pk, self.version.pk, 'sphinx', epub=True
        )

        # pdf is cleaned
        rmtree.assert_called_once()
        args, _ = rmtree.call_args
        self.assertIn('pdf', args[0])

        # Artifacts are copied to the media directory
        copy.assert_called_once()
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx_epub', args[0])
        self.assertIn('media/epub', args[1])

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_localmedia(self, rmtree, copy):
        sync_files(
            self.project.pk, self.version.pk, 'sphinx', localmedia=True
        )
        pdf, epub = rmtree.call_args_list

        # pdf and epub are cleaned
        args, _ = pdf
        self.assertIn('pdf', args[0])
        args, _ = epub
        self.assertIn('epub', args[0])

        # Artifacts are copied to the media directory
        copy.assert_called_once()
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx_localmedia', args[0])
        self.assertIn('media/htmlzip', args[1])

    @patch('readthedocs.builds.syncers.Syncer.copy')
    @patch('readthedocs.projects.tasks.shutil.rmtree')
    def test_sync_files_search(self, rmtree, copy):
        sync_files(
            self.project.pk, self.version.pk, 'sphinx', search=True
        )
        pdf, epub = rmtree.call_args_list

        # pdf and epub are cleaned
        args, _ = pdf
        self.assertIn('pdf', args[0])
        args, _ = epub
        self.assertIn('epub', args[0])

        # Artifacts are copied to the media directory
        copy.assert_called_once()
        args, _ = copy.call_args
        self.assertIn('artifacts', args[0])
        self.assertIn('sphinx_search', args[0])
        self.assertIn('media/json', args[1])
