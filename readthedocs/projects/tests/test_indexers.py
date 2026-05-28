from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.search import (
    FileManifestIndexer,
    SearchIndexer,
    _get_indexers,
)


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


class TestFileManifestIndexerCollect(TestCase):
    """Pinning down behavior of FileManifestIndexer.collect() for the diff feature."""

    def setUp(self):
        self.project = get(Project)
        self.version = self.project.versions.get(slug=LATEST)
        self.build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )

    @mock.patch("readthedocs.projects.tasks.search.write_manifest")
    @mock.patch("readthedocs.projects.tasks.search.snapshot_previous_manifest")
    def test_snapshot_runs_before_write_manifest(
        self, snapshot_previous, write_manifest
    ):
        """The previous-manifest snapshot MUST be taken before the new manifest
        overwrites it; reversing the order would snapshot the new manifest and
        produce an empty diff."""
        calls = []
        snapshot_previous.side_effect = lambda *a, **kw: calls.append("snapshot")
        write_manifest.side_effect = lambda *a, **kw: calls.append("write")

        indexer = FileManifestIndexer(
            version=self.version, build=self.build, post_build_overview=False
        )
        indexer.collect(sync_id=1)
        assert calls == ["snapshot", "write"]

    @mock.patch("readthedocs.projects.tasks.search.write_manifest")
    @mock.patch("readthedocs.projects.tasks.search.snapshot_previous_manifest")
    def test_snapshot_passes_new_build_id_for_reindex_guard(
        self, snapshot_previous, write_manifest
    ):
        """The collect call must hand the new build id to snapshot_previous_manifest
        so re-indexing the same build doesn't refresh the snapshot."""
        indexer = FileManifestIndexer(
            version=self.version, build=self.build, post_build_overview=False
        )
        indexer.collect(sync_id=1)
        snapshot_previous.assert_called_once_with(
            self.version, new_build_id=self.build.id
        )
