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
    """`FileManifestIndexer.collect` writes manifests and pins PR diff bases."""

    def setUp(self):
        self.project = get(Project)
        self.base_version = self.project.versions.get(slug=LATEST)
        self.base_build = get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )

    @mock.patch("readthedocs.projects.tasks.search.write_manifest")
    def test_collect_writes_per_build_manifest_for_normal_version(self, write_manifest):
        normal_build = get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        indexer = FileManifestIndexer(
            version=self.base_version,
            build=normal_build,
            post_build_overview=False,
        )
        indexer._hashes = {"index.html": "hash"}
        indexer.collect(sync_id=1)
        write_manifest.assert_called_once_with(normal_build, {"index.html": "hash"})

    @mock.patch("readthedocs.projects.tasks.search.write_manifest")
    def test_collect_pins_diff_base_on_first_pr_build(self, write_manifest):
        pr_version = get(
            Version,
            project=self.project,
            slug="pr-1",
            type=EXTERNAL,
            active=True,
            built=True,
        )
        pr_build = get(
            Build,
            project=self.project,
            version=pr_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        indexer = FileManifestIndexer(
            version=pr_version,
            build=pr_build,
            post_build_overview=False,
        )
        indexer._hashes = {}
        indexer.collect(sync_id=1)

        pr_build.refresh_from_db()
        assert pr_build.diff_base_build_id == self.base_build.id

    @mock.patch("readthedocs.projects.tasks.search.write_manifest")
    def test_collect_does_not_overwrite_existing_diff_base(self, write_manifest):
        pinned_to = get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        pr_version = get(
            Version,
            project=self.project,
            slug="pr-2",
            type=EXTERNAL,
            active=True,
            built=True,
        )
        pr_build = get(
            Build,
            project=self.project,
            version=pr_version,
            state=BUILD_STATE_FINISHED,
            success=True,
            diff_base_build=pinned_to,
        )
        # A newer base build exists; the existing pin must not be moved.
        get(
            Build,
            project=self.project,
            version=self.base_version,
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        indexer = FileManifestIndexer(
            version=pr_version,
            build=pr_build,
            post_build_overview=False,
        )
        indexer._hashes = {}
        indexer.collect(sync_id=1)

        pr_build.refresh_from_db()
        assert pr_build.diff_base_build_id == pinned_to.id
