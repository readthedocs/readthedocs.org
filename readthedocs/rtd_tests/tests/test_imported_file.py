import os
from unittest import mock

import pytest
from django.conf import settings
from readthedocs.storage import get_storage_class
from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifest, FileTreeDiffManifestFile
from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.tasks.search import index_build
from readthedocs.search.documents import PageDocument

base_dir = os.path.dirname(os.path.dirname(__file__))


@pytest.mark.search
@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class ImportedFileTests(TestCase):
    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

    def setUp(self):
        self.project = get(Project)

        # Disable File Tree Diff because these tests are not prepared
        self.project.addons.filetreediff_enabled = False
        self.project.addons.save()

        self.version = self.project.versions.get(slug=LATEST)
        self.build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )

        self.test_dir = os.path.join(base_dir, "files")
        with override_settings(DOCROOT=self.test_dir):
            self._copy_storage_dir(self.version)

        self._create_index()

    def _create_index(self):
        try:
            PageDocument.init()
        except Exception:
            # If the index already exists, the init fails.
            pass

    def tearDown(self):
        # Delete index
        PageDocument._index.delete(ignore=404)

    def _copy_storage_dir(self, version):
        """Copy the test directory (rtd_tests/files) to storage"""
        self.storage.copy_directory(
            self.test_dir,
            self.project.get_storage_path(
                type_="html",
                version_slug=version.slug,
                include_file=False,
                version_type=version.type,
            ),
        )

    def test_properly_created(self):
        """
        Only 4 files in the directory are HTML

        - index.html
        - test.html
        - api/index.html
        - 404.html

        But we create imported files for index.html and 404.html files only.
        """
        self.assertEqual(ImportedFile.objects.count(), 0)

        sync_id = index_build(self.build.pk)
        self.assertEqual(ImportedFile.objects.count(), 3)
        self.assertEqual(
            set(HTMLFile.objects.all().values_list("path", flat=True)),
            {"index.html", "api/index.html", "404.html"},
        )

        results = PageDocument().search().filter("term", build=sync_id).execute()
        self.assertEqual(
            {result.path for result in results},
            {"index.html", "404.html", "test.html", "api/index.html"},
        )

        sync_id = index_build(self.build.pk)
        self.assertEqual(ImportedFile.objects.count(), 3)
        self.assertEqual(
            set(HTMLFile.objects.all().values_list("path", flat=True)),
            {"index.html", "api/index.html", "404.html"},
        )

        results = PageDocument().search().filter("term", build=sync_id).execute()
        self.assertEqual(
            {result.path for result in results},
            {"index.html", "404.html", "test.html", "api/index.html"},
        )

    def test_index_external_version(self):
        self.assertEqual(ImportedFile.objects.count(), 0)
        self.version.type = EXTERNAL
        self.version.save()

        with override_settings(DOCROOT=self.test_dir):
            self._copy_storage_dir(self.version)

        sync_id = index_build(self.build.pk)
        self.assertEqual(ImportedFile.objects.count(), 3)
        self.assertEqual(
            set(HTMLFile.objects.all().values_list("path", flat=True)),
            {"index.html", "api/index.html", "404.html"},
        )

        results = PageDocument().search().filter("term", build=sync_id).execute()
        self.assertEqual(len(results), 0)

        sync_id = index_build(self.build.pk)
        self.assertEqual(ImportedFile.objects.count(), 3)
        self.assertEqual(
            set(HTMLFile.objects.all().values_list("path", flat=True)),
            {"index.html", "api/index.html", "404.html"},
        )

        self.assertEqual(len(results), 0)

    def test_update_build(self):
        self.assertEqual(ImportedFile.objects.count(), 0)
        sync_id = index_build(self.build.pk)
        for obj in ImportedFile.objects.all():
            self.assertEqual(obj.build, sync_id)

        results = PageDocument().search().filter().execute()
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result.build, sync_id)

        sync_id = index_build(self.build.pk)
        for obj in ImportedFile.objects.all():
            self.assertEqual(obj.build, sync_id)

        # NOTE: we can't test that the files from the previous build
        # were deleted, since deletion happens asynchronously.
        results = PageDocument().search().filter("term", build=sync_id).execute()
        self.assertEqual(len(results), 4)

    def test_page_default_rank(self):
        self.assertEqual(HTMLFile.objects.count(), 0)
        sync_id = index_build(self.build.pk)

        results = (
            PageDocument()
            .search()
            .filter("term", project=self.project.slug)
            .filter("term", version=self.version.slug)
            .execute()
        )
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result.project, self.project.slug)
            self.assertEqual(result.version, self.version.slug)
            self.assertEqual(result.build, sync_id)
            self.assertEqual(result.rank, 0)

    def test_page_custom_rank_glob(self):
        self.build.config = {
            "search": {
                "ranking": {
                    "*index.html": 5,
                }
            }
        }
        self.build.save()
        sync_id = index_build(self.build.pk)

        results = (
            PageDocument()
            .search()
            .filter("term", project=self.project.slug)
            .filter("term", version=self.version.slug)
            .execute()
        )
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result.project, self.project.slug)
            self.assertEqual(result.version, self.version.slug)
            self.assertEqual(result.build, sync_id)
            if result.path.endswith("index.html"):
                self.assertEqual(result.rank, 5, result.path)
            else:
                self.assertEqual(result.rank, 0, result.path)

    def test_page_custom_rank_several(self):
        self.build.config = {
            "search": {
                "ranking": {
                    "test.html": 5,
                    "api/index.html": 2,
                }
            }
        }
        self.build.save()
        sync_id = index_build(self.build.pk)

        results = (
            PageDocument()
            .search()
            .filter("term", project=self.project.slug)
            .filter("term", version=self.version.slug)
            .execute()
        )
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result.project, self.project.slug)
            self.assertEqual(result.version, self.version.slug)
            self.assertEqual(result.build, sync_id)
            if result.path == "test.html":
                self.assertEqual(result.rank, 5)
            elif result.path == "api/index.html":
                self.assertEqual(result.rank, 2)
            else:
                self.assertEqual(result.rank, 0)

    def test_page_custom_rank_precedence(self):
        self.build.config = {
            "search": {
                "ranking": {
                    "*.html": 5,
                    "api/index.html": 2,
                }
            }
        }
        self.build.save()
        sync_id = index_build(self.build.pk)

        results = (
            PageDocument()
            .search()
            .filter("term", project=self.project.slug)
            .filter("term", version=self.version.slug)
            .execute()
        )
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result.project, self.project.slug)
            self.assertEqual(result.version, self.version.slug)
            self.assertEqual(result.build, sync_id)
            if result.path == "api/index.html":
                self.assertEqual(result.rank, 2, result.path)
            else:
                self.assertEqual(result.rank, 5, result.path)

    def test_page_custom_rank_precedence_inverted(self):
        self.build.config = {
            "search": {
                "ranking": {
                    "api/index.html": 2,
                    "*.html": 5,
                }
            }
        }
        self.build.save()
        sync_id = index_build(self.build.pk)

        results = (
            PageDocument()
            .search()
            .filter("term", project=self.project.slug)
            .filter("term", version=self.version.slug)
            .execute()
        )
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result.project, self.project.slug)
            self.assertEqual(result.version, self.version.slug)
            self.assertEqual(result.build, sync_id)
            self.assertEqual(result.rank, 5)

    def test_search_page_ignore(self):
        self.build.config = {
            "search": {
                "ignore": ["api/index.html"],
            }
        }
        self.build.save()
        index_build(self.build.pk)

        self.assertEqual(
            set(HTMLFile.objects.all().values_list("path", flat=True)),
            {"index.html", "api/index.html", "404.html"},
        )
        results = (
            PageDocument()
            .search()
            .filter("term", project=self.project.slug)
            .filter("term", version=self.version.slug)
            .execute()
        )
        self.assertEqual(len(results), 3)
        self.assertEqual(
            {result.path for result in results}, {"index.html", "404.html", "test.html"}
        )

    def test_update_content(self):
        test_dir = os.path.join(base_dir, "files")
        self.assertEqual(ImportedFile.objects.count(), 0)

        with open(os.path.join(test_dir, "test.html"), "w+") as f:
            f.write("Woo")

        with override_settings(DOCROOT=self.test_dir):
            self._copy_storage_dir(self.version)

        sync_id = index_build(self.build.pk)
        self.assertEqual(ImportedFile.objects.count(), 3)
        document = (
            PageDocument()
            .search()
            .filter("term", project=self.project.slug)
            .filter("term", version=self.version.slug)
            .filter("term", path="test.html")
            .filter("term", build=sync_id)
            .execute()[0]
        )
        self.assertEqual(document.sections[0].content, "Woo")

        with open(os.path.join(test_dir, "test.html"), "w+") as f:
            f.write("Something Else")

        with override_settings(DOCROOT=self.test_dir):
            self._copy_storage_dir(self.version)

        sync_id = index_build(self.build.pk)
        self.assertEqual(ImportedFile.objects.count(), 3)
        document = (
            PageDocument()
            .search()
            .filter("term", project=self.project.slug)
            .filter("term", version=self.version.slug)
            .filter("term", path="test.html")
            .filter("term", build=sync_id)
            .execute()[0]
        )
        self.assertEqual(document.sections[0].content, "Something Else")

    @mock.patch("readthedocs.projects.tasks.search.write_manifest")
    def test_create_file_tree_manifest(self, write_manifest):
        assert self.version.slug == LATEST

        self.project.addons.filetreediff_enabled = True
        self.project.addons.save()

        index_build(self.build.pk)
        manifest = FileTreeDiffManifest(
            build_id=self.build.pk,
            files=[
                FileTreeDiffManifestFile(
                    path="index.html",
                    main_content_hash=mock.ANY,
                ),
                FileTreeDiffManifestFile(
                    path="404.html",
                    main_content_hash=mock.ANY,
                ),
                FileTreeDiffManifestFile(
                    path="test.html",
                    main_content_hash=mock.ANY,
                ),
                FileTreeDiffManifestFile(
                    path="api/index.html",
                    main_content_hash=mock.ANY,
                ),
            ],
        )
        write_manifest.assert_called_once_with(self.version, manifest)

        # The version is not the latest nor a PR.
        new_version = get(
            Version,
            project=self.project,
            slug="new-version",
        )
        self.build.version = new_version
        self.build.save()
        write_manifest.reset_mock()
        index_build(self.build.pk)
        write_manifest.assert_not_called()

        # Now it is a PR.
        new_version.type = EXTERNAL
        new_version.save()
        with override_settings(DOCROOT=self.test_dir):
            self._copy_storage_dir(new_version)
        write_manifest.reset_mock()
        index_build(self.build.pk)
        write_manifest.assert_called_once_with(new_version, manifest)
