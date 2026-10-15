from unittest import mock

from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import GitHubAppInstallation, RemoteRepository
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.search import (
    FileManifestIndexer,
    SearchIndexer,
    _get_indexers,
    _should_create_manifest,
)


class TestShouldCreateManifest(TestCase):
    def setUp(self):
        self.project = get(Project)

    def _external_version(self):
        return get(Version, project=self.project, slug="123", type=EXTERNAL)

    def _disable_manifest_features(self):
        self.project.addons.filetreediff_enabled = False
        self.project.addons.save()
        self.project.show_build_overview_in_comment = False
        self.project.save()

    def test_base_version(self):
        version = self.project.versions.get(slug=LATEST)
        assert _should_create_manifest(version) is True

    def test_base_version_with_features_disabled(self):
        # The base version's manifest is always kept fresh: a stale one would
        # become the baseline of pull request diffs.
        self._disable_manifest_features()
        version = self.project.versions.get(slug=LATEST)
        assert _should_create_manifest(version) is True

    def test_external_version(self):
        assert _should_create_manifest(self._external_version()) is True

    def test_non_base_internal_version(self):
        version = get(Version, project=self.project, slug="stable")
        assert _should_create_manifest(version) is False

    def test_custom_base_version(self):
        version = get(Version, project=self.project, slug="main")
        self.project.addons.options_base_version = version
        self.project.addons.save()

        assert _should_create_manifest(version) is True
        assert _should_create_manifest(self.project.versions.get(slug=LATEST)) is False

    def test_external_version_with_features_disabled(self):
        self._disable_manifest_features()
        assert _should_create_manifest(self._external_version()) is False

    def test_build_overview_needs_the_github_app(self):
        # ``show_build_overview_in_comment`` defaults to True but is only
        # honored (and only editable) for GitHub App projects.
        self.project.addons.filetreediff_enabled = False
        self.project.addons.save()
        self.project.show_build_overview_in_comment = True
        self.project.save()
        version = self._external_version()

        assert _should_create_manifest(version) is False

        self.project.remote_repository = get(
            RemoteRepository,
            vcs_provider=GITHUB_APP,
            github_app_installation=get(GitHubAppInstallation),
            remote_id="12345",
        )
        self.project.save()
        assert _should_create_manifest(version) is True

    @override_settings(RTD_FILETREEDIFF_ALL=True)
    def test_filetreediff_all_overrides_everything(self):
        self._disable_manifest_features()
        version = get(Version, project=self.project, slug="stable")
        assert _should_create_manifest(version) is True

    def test_manifest_indexer_skipped_when_features_disabled(self):
        self._disable_manifest_features()
        build = get(
            Build,
            version=self._external_version(),
            state=BUILD_STATE_FINISHED,
            success=True,
        )

        indexers = _get_indexers(version=build.version, build=build)

        assert not any(isinstance(indexer, FileManifestIndexer) for indexer in indexers)

    def test_manifest_indexer_created_by_default(self):
        build = get(
            Build,
            version=self._external_version(),
            state=BUILD_STATE_FINISHED,
            success=True,
        )

        indexers = _get_indexers(version=build.version, build=build)

        assert any(isinstance(indexer, FileManifestIndexer) for indexer in indexers)


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
