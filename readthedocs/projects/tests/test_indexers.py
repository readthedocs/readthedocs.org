from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.search import FileManifestIndexer, SearchIndexer, _get_indexers


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


class TestFileManifestIndexer(TestCase):
    """The base version of the project needs a manifest to diff against."""

    def _has_manifest_indexer(self, version):
        build = get(Build, version=version, state=BUILD_STATE_FINISHED, success=True)
        indexers = _get_indexers(version=version, build=build)
        return any(isinstance(indexer, FileManifestIndexer) for indexer in indexers)

    def test_manifest_created_for_latest(self):
        project = get(Project)
        latest = project.versions.get(slug=LATEST)
        latest.active = True
        latest.built = True
        latest.save()
        assert self._has_manifest_indexer(latest)

    def test_manifest_not_created_for_other_versions(self):
        project = get(Project)
        latest = project.versions.get(slug=LATEST)
        latest.active = True
        latest.built = True
        latest.save()
        version = get(Version, project=project, slug="v2", active=True, built=True)
        assert not self._has_manifest_indexer(version)

    def test_manifest_created_for_default_branch_when_latest_is_not_built(self):
        """Uploaded projects publish the branch itself, not ``latest``."""
        project = get(Project, default_branch="main")
        project.versions.filter(slug=LATEST).update(built=False)
        main = get(Version, project=project, slug="main", verbose_name="main", active=True, built=True)
        assert self._has_manifest_indexer(main)

    def test_manifest_created_for_configured_base_version(self):
        project = get(Project)
        version = get(Version, project=project, slug="v2", active=True, built=True)
        project.addons.options_base_version = version
        project.addons.save()
        assert self._has_manifest_indexer(version)


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
