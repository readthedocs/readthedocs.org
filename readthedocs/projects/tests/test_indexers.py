import os
import tempfile
from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.search import FileManifestIndexer
from readthedocs.projects.tasks.search import IndexFileIndexer
from readthedocs.projects.tasks.search import Indexer
from readthedocs.projects.tasks.search import SearchIndexer
from readthedocs.projects.tasks.search import _get_indexers
from readthedocs.projects.tasks.search import _process_files


class TestSearchIndexing(TestCase):
    """Tests for search_indexing_enabled field behavior."""

    def test_search_indexer_not_created_when_disabled(self):
        project = get(Project, search_indexing_enabled=False)
        version = project.versions.first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        # Check that no SearchIndexer is in the list
        search_indexers = [
            indexer for indexer in indexers if isinstance(indexer, SearchIndexer)
        ]
        assert len(search_indexers) == 0

    def test_search_indexer_created_when_enabled(self):
        """Test that SearchIndexer is created when search_indexing_enabled is True."""
        project = get(
            Project,
            search_indexing_enabled=True,
        )
        version = project.versions.first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        # Check that SearchIndexer is in the list
        search_indexers = [
            indexer for indexer in indexers if isinstance(indexer, SearchIndexer)
        ]
        assert len(search_indexers) == 1

    def test_search_indexer_not_created_for_delisted_project(self):
        """Test that SearchIndexer is not created for delisted projects."""
        project = get(
            Project,
            delisted=True,
        )
        version = project.versions.first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        # Check that no SearchIndexer is in the list
        search_indexers = [
            indexer for indexer in indexers if isinstance(indexer, SearchIndexer)
        ]
        assert len(search_indexers) == 0

    def test_search_indexer_not_created_for_external_version(self):
        """Test that SearchIndexer is not created for external versions."""
        project = get(Project)
        version = get(Version, project=project, slug="123", built=True, type=EXTERNAL)
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        # Check that no SearchIndexer is in the list
        search_indexers = [
            indexer for indexer in indexers if isinstance(indexer, SearchIndexer)
        ]
        assert len(search_indexers) == 0


@mock.patch("readthedocs.projects.tasks.search.search_index_updated")
@mock.patch("readthedocs.projects.tasks.search.remove_indexed_files")
class TestSearchIndexUpdatedSignal(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)

    def _get_indexer(self, **kwargs):
        return SearchIndexer(
            project=self.project,
            version=self.version,
            search_ranking={},
            search_ignore=[],
            **kwargs,
        )

    def test_collect_sends_search_index_updated(self, remove_indexed_files, search_index_updated):
        self._get_indexer().collect(sync_id=1)

        search_index_updated.send.assert_called_once_with(
            sender=Project,
            project=self.project,
            version=self.version,
        )

    def test_collect_into_custom_index_does_not_send_signal(
        self, remove_indexed_files, search_index_updated
    ):
        self._get_indexer(search_index_name="new-index").collect(sync_id=1)

        search_index_updated.send.assert_not_called()


class RecordingIndexer(Indexer):
    def __init__(self, needs_sections):
        self.needs_sections = needs_sections
        self.processed_json = []

    def process(self, html_file, sync_id):
        self.processed_json.append(html_file.processed_json)

    def collect(self, sync_id):
        pass


class TestProcessFilesSections(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = self.project.versions.first()

    def _download(self, storage_path, local_path, include=None):
        with open(os.path.join(local_path, "index.html"), "w") as f:
            f.write(
                '<html><body><div role="main">'
                '<h1 id="title">Title</h1><p>Content</p>'
                "</div></body></html>"
            )

    def _process(self, indexers):
        with (
            tempfile.TemporaryDirectory() as tmp_dir,
            mock.patch(
                "readthedocs.projects.tasks.search.build_media_storage.rclone_download_directory",
                side_effect=self._download,
            ),
        ):
            _process_files(version=self.version, indexers=indexers, local_path=tmp_dir)

    def test_only_search_indexer_needs_sections(self):
        assert SearchIndexer.needs_sections is True
        assert FileManifestIndexer.needs_sections is False
        assert IndexFileIndexer.needs_sections is False

    def test_sections_are_skipped_when_no_indexer_needs_them(self):
        indexer = RecordingIndexer(needs_sections=False)

        self._process([indexer])

        [processed_json] = indexer.processed_json
        assert processed_json["title"] == "Title"
        assert processed_json["sections"] == []
        assert processed_json["main_content_hash"] is not None
        assert processed_json["text_hash"] is not None
        assert processed_json["markup_hash"] is not None

    def test_sections_are_parsed_when_an_indexer_needs_them(self):
        without_sections = RecordingIndexer(needs_sections=False)
        with_sections = RecordingIndexer(needs_sections=True)

        self._process([without_sections, with_sections])

        # Both indexers share the same parsed page.
        assert without_sections.processed_json == with_sections.processed_json
        [processed_json] = with_sections.processed_json
        assert processed_json["sections"] == [
            {"id": "title", "title": "Title", "content": "Content"}
        ]
