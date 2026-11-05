from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.filetreediff.dataclasses import FileTreeDiffManifest
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.search import (
    FileManifestIndexer,
    SearchIndexer,
    _get_indexers,
    process_builder_manifest,
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


@mock.patch("readthedocs.projects.tasks.search.get_manifest")
class TestFileManifestIndexerCreation(TestCase):
    """The manifest is only regenerated when the build didn't upload its own."""

    def setUp(self):
        self.project = get(Project)
        self.version = self.project.versions.get(slug=LATEST)
        self.build = get(Build, version=self.version, state=BUILD_STATE_FINISHED, success=True)

    def _manifest_indexers(self):
        indexers = _get_indexers(version=self.version, build=self.build)
        return [indexer for indexer in indexers if isinstance(indexer, FileManifestIndexer)]

    def test_indexer_created_when_no_manifest(self, get_manifest):
        get_manifest.return_value = None
        assert len(self._manifest_indexers()) == 1

    def test_indexer_created_when_manifest_is_from_previous_build(self, get_manifest):
        get_manifest.return_value = FileTreeDiffManifest(build_id=self.build.id - 1, files=[])
        assert len(self._manifest_indexers()) == 1

    def test_indexer_skipped_when_build_uploaded_manifest(self, get_manifest):
        get_manifest.return_value = FileTreeDiffManifest(build_id=self.build.id, files=[])
        assert len(self._manifest_indexers()) == 0

    def test_manifest_not_checked_for_non_base_versions(self, get_manifest):
        version = get(Version, project=self.project, slug="stable")
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        indexers = _get_indexers(version=version, build=build)

        assert not any(isinstance(indexer, FileManifestIndexer) for indexer in indexers)
        get_manifest.assert_not_called()


@mock.patch("readthedocs.projects.tasks.search._manifest_side_effects")
@mock.patch("readthedocs.projects.tasks.search.get_manifest")
class TestProcessBuilderManifest(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = self.project.versions.get(slug=LATEST)
        self.build = get(Build, version=self.version, state=BUILD_STATE_FINISHED, success=True)

    def test_side_effects_run_for_build_manifest(self, get_manifest, _manifest_side_effects):
        get_manifest.return_value = FileTreeDiffManifest(build_id=self.build.id, files=[])

        process_builder_manifest(self.build.pk)

        _manifest_side_effects.assert_called_once_with(self.version, self.build)

    def test_noop_without_manifest(self, get_manifest, _manifest_side_effects):
        get_manifest.return_value = None

        process_builder_manifest(self.build.pk)

        _manifest_side_effects.assert_not_called()

    def test_noop_when_manifest_is_from_previous_build(self, get_manifest, _manifest_side_effects):
        get_manifest.return_value = FileTreeDiffManifest(build_id=self.build.id - 1, files=[])

        process_builder_manifest(self.build.pk)

        _manifest_side_effects.assert_not_called()

    def test_noop_when_build_does_not_exist(self, get_manifest, _manifest_side_effects):
        process_builder_manifest(self.build.pk + 999)

        get_manifest.assert_not_called()
        _manifest_side_effects.assert_not_called()

    def test_noop_for_non_base_versions(self, get_manifest, _manifest_side_effects):
        version = get(Version, project=self.project, slug="stable")
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)

        process_builder_manifest(build.pk)

        get_manifest.assert_not_called()
        _manifest_side_effects.assert_not_called()


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
