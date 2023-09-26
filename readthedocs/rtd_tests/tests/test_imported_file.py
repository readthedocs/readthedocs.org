import os

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.tasks.search import _create_imported_files_and_search_index
from readthedocs.search.documents import PageDocument

base_dir = os.path.dirname(os.path.dirname(__file__))


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class ImportedFileTests(TestCase):
    fixtures = ["eric", "test_data"]

    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

    def setUp(self):
        self.project = Project.objects.get(slug="pip")
        self.version = self.project.versions.first()

        self.test_dir = os.path.join(base_dir, "files")
        with override_settings(DOCROOT=self.test_dir):
            self._copy_storage_dir()

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

    def _manage_imported_files(self, version, search_ranking=None, search_ignore=None):
        """Helper function for the tests to create and sync ImportedFiles."""
        search_ranking = search_ranking or {}
        search_ignore = search_ignore or []
        return _create_imported_files_and_search_index(
            version=version,
            search_ranking=search_ranking,
            search_ignore=search_ignore,
        )

    def _copy_storage_dir(self):
        """Copy the test directory (rtd_tests/files) to storage"""
        self.storage.copy_directory(
            self.test_dir,
            self.project.get_storage_path(
                type_="html",
                version_slug=self.version.slug,
                include_file=False,
                version_type=self.version.type,
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

        sync_id = self._manage_imported_files(version=self.version)
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

        sync_id = self._manage_imported_files(version=self.version)
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
            self._copy_storage_dir()

        sync_id = self._manage_imported_files(version=self.version)
        self.assertEqual(ImportedFile.objects.count(), 3)
        self.assertEqual(
            set(HTMLFile.objects.all().values_list("path", flat=True)),
            {"index.html", "api/index.html", "404.html"},
        )

        results = PageDocument().search().filter("term", build=sync_id).execute()
        self.assertEqual(len(results), 0)

        sync_id = self._manage_imported_files(version=self.version)
        self.assertEqual(ImportedFile.objects.count(), 3)
        self.assertEqual(
            set(HTMLFile.objects.all().values_list("path", flat=True)),
            {"index.html", "api/index.html", "404.html"},
        )

        self.assertEqual(len(results), 0)

    def test_update_build(self):
        self.assertEqual(ImportedFile.objects.count(), 0)
        sync_id = self._manage_imported_files(self.version)
        for obj in ImportedFile.objects.all():
            self.assertEqual(obj.build, sync_id)

        results = PageDocument().search().filter().execute()
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result.build, sync_id)

        sync_id = self._manage_imported_files(self.version)
        for obj in ImportedFile.objects.all():
            self.assertEqual(obj.build, sync_id)

        # NOTE: we can't test that the files from the previous build
        # were deleted, since deletion happens asynchronously.
        results = PageDocument().search().filter("term", build=sync_id).execute()
        self.assertEqual(len(results), 4)

    def test_page_default_rank(self):
        search_ranking = {}
        self.assertEqual(HTMLFile.objects.count(), 0)
        sync_id = self._manage_imported_files(
            self.version, search_ranking=search_ranking
        )

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
        search_ranking = {
            "*index.html": 5,
        }
        sync_id = self._manage_imported_files(
            self.version, search_ranking=search_ranking
        )

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
        search_ranking = {
            "test.html": 5,
            "api/index.html": 2,
        }
        sync_id = self._manage_imported_files(
            self.version, search_ranking=search_ranking
        )

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
        search_ranking = {
            "*.html": 5,
            "api/index.html": 2,
        }
        sync_id = self._manage_imported_files(
            self.version, search_ranking=search_ranking
        )

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
        search_ranking = {
            "api/index.html": 2,
            "*.html": 5,
        }
        sync_id = self._manage_imported_files(
            self.version, search_ranking=search_ranking
        )

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
        search_ignore = ["api/index.html"]
        self._manage_imported_files(
            self.version,
            search_ignore=search_ignore,
        )

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
            self._copy_storage_dir()

        sync_id = self._manage_imported_files(self.version)
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
            self._copy_storage_dir()

        sync_id = self._manage_imported_files(self.version)
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
