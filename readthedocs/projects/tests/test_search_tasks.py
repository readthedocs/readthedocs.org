"""Tests for project search tasks."""

from unittest import mock

import pytest
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.projects.tasks.search import (
    _get_indexers,
    index_build,
    remove_search_indexes,
    SearchIndexer,
)
from readthedocs.search.utils import remove_indexed_files


@pytest.mark.django_db
@pytest.mark.search
class TestRemoveSearchIndexesTask:
    """Tests for the remove_search_indexes task."""

    @mock.patch("readthedocs.projects.tasks.search.remove_indexed_files")
    def test_remove_search_indexes_for_project(self, mock_remove_indexed_files):
        """Test that remove_search_indexes removes all indexes for a project."""
        project = get(Project, slug="test-project")

        remove_search_indexes(project_slug=project.slug)

        mock_remove_indexed_files.assert_called_once_with(
            project_slug=project.slug,
            version_slug=None,
        )

    @mock.patch("readthedocs.projects.tasks.search.remove_indexed_files")
    def test_remove_search_indexes_for_version(self, mock_remove_indexed_files):
        """Test that remove_search_indexes removes indexes for a specific version."""
        project = get(Project, slug="test-project")
        version = get(Version, project=project, slug="v1.0")

        remove_search_indexes(project_slug=project.slug, version_slug=version.slug)

        mock_remove_indexed_files.assert_called_once_with(
            project_slug=project.slug,
            version_slug=version.slug,
        )


@pytest.mark.django_db
@pytest.mark.search
class TestSearchIndexingEnabled:
    """Tests for search_indexing_enabled field behavior."""

    def test_search_indexer_not_created_when_disabled(self):
        """Test that SearchIndexer is not created when search_indexing_enabled is False."""
        project = get(Project, search_indexing_enabled=False)
        version = project.versions.first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        # Check that no SearchIndexer is in the list
        search_indexers = [indexer for indexer in indexers if isinstance(indexer, SearchIndexer)]
        assert len(search_indexers) == 0

    def test_search_indexer_created_when_enabled(self):
        """Test that SearchIndexer is created when search_indexing_enabled is True."""
        project = get(
            Project,
            search_indexing_enabled=True,
            privacy_level=PUBLIC,
            delisted=False,
        )
        version = project.versions.filter(type="branch").first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        # Check that SearchIndexer is in the list
        search_indexers = [indexer for indexer in indexers if isinstance(indexer, SearchIndexer)]
        assert len(search_indexers) == 1

    def test_search_indexer_not_created_for_delisted_project(self):
        """Test that SearchIndexer is not created for delisted projects."""
        project = get(
            Project,
            search_indexing_enabled=True,
            privacy_level=PUBLIC,
            delisted=True,
        )
        version = project.versions.filter(type="branch").first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        # Check that no SearchIndexer is in the list
        search_indexers = [indexer for indexer in indexers if isinstance(indexer, SearchIndexer)]
        assert len(search_indexers) == 0

    def test_search_indexer_not_created_for_external_version(self):
        """Test that SearchIndexer is not created for external versions."""
        project = get(
            Project,
            search_indexing_enabled=True,
            privacy_level=PUBLIC,
            delisted=False,
        )
        version = get(Version, project=project, slug="pr-123", built=True, type="external")
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        # Check that no SearchIndexer is in the list
        search_indexers = [indexer for indexer in indexers if isinstance(indexer, SearchIndexer)]
        assert len(search_indexers) == 0

    @mock.patch("readthedocs.projects.tasks.search._process_files")
    @mock.patch("readthedocs.projects.tasks.search._get_indexers")
    def test_index_build_respects_search_indexing_enabled(
        self, mock_get_indexers, mock_process_files
    ):
        """Test that index_build respects search_indexing_enabled field."""
        project = get(Project, search_indexing_enabled=False)
        version = project.versions.first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        # Mock to return empty indexers list (simulating disabled search)
        mock_get_indexers.return_value = []

        index_build(build_id=build.pk)

        # Verify that _get_indexers was called
        mock_get_indexers.assert_called_once()
        # Verify that _process_files was called even with empty indexers
        mock_process_files.assert_called_once()


@pytest.mark.django_db
@pytest.mark.search
class TestSearchIndexerIntegration:
    """Integration tests for search indexing with search_indexing_enabled field."""

    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        """Set up test environment."""
        settings.ELASTICSEARCH_DSL_AUTOSYNC = True

    @mock.patch("readthedocs.search.utils.DEDConfig.autosync_enabled")
    @mock.patch("readthedocs.search.documents.PageDocument.update")
    @mock.patch("readthedocs.storage.build_media_storage.walk")
    @mock.patch("readthedocs.storage.build_media_storage.join")
    def test_no_search_indexing_when_disabled(
        self,
        mock_join,
        mock_walk,
        mock_page_update,
        mock_autosync,
    ):
        """Test that no search indexing occurs when search_indexing_enabled is False."""
        mock_autosync.return_value = True

        project = get(
            Project,
            search_indexing_enabled=False,
            privacy_level=PUBLIC,
        )
        version = project.versions.filter(type="branch").first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        # Mock file system walk to return some HTML files
        mock_walk.return_value = [("storage/html/", [], ["index.html", "page.html"])]
        mock_join.side_effect = lambda root, filename: f"{root}{filename}"

        index_build(build_id=build.pk)

        # Verify that PageDocument.update was never called (no indexing)
        mock_page_update.assert_not_called()

    @mock.patch("readthedocs.search.utils.DEDConfig.autosync_enabled")
    @mock.patch("readthedocs.search.documents.PageDocument.update")
    @mock.patch("readthedocs.storage.build_media_storage.walk")
    @mock.patch("readthedocs.storage.build_media_storage.join")
    def test_search_indexing_when_enabled(
        self,
        mock_join,
        mock_walk,
        mock_page_update,
        mock_autosync,
    ):
        """Test that search indexing occurs when search_indexing_enabled is True."""
        mock_autosync.return_value = True

        project = get(
            Project,
            search_indexing_enabled=True,
            privacy_level=PUBLIC,
            delisted=False,
        )
        version = project.versions.filter(type="branch").first()
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        # Mock file system walk to return some HTML files
        mock_walk.return_value = [("storage/html/", [], ["index.html", "page.html"])]
        mock_join.side_effect = lambda root, filename: f"{root}{filename}"

        index_build(build_id=build.pk)

        # Verify that PageDocument.update was called (indexing happened)
        assert mock_page_update.call_count > 0
