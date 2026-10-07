import os
import tempfile
import time
from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.search import (
    LOCAL_COPY_MAX_AGE_SECONDS,
    LOCAL_COPY_PREFIX,
    SearchIndexer,
    _get_indexers,
    _remove_stale_local_copies,
)


class TestRemoveStaleLocalCopies(TestCase):
    def _make_dir(self, root, name, age_seconds=0):
        path = os.path.join(root, name)
        os.makedirs(os.path.join(path, "nested"))
        if age_seconds:
            stamp = time.time() - age_seconds
            os.utime(path, (stamp, stamp))
        return path

    def test_removes_only_stale_local_copies(self):
        tmp_root = tempfile.mkdtemp()
        stale = self._make_dir(
            tmp_root, f"{LOCAL_COPY_PREFIX}old", age_seconds=LOCAL_COPY_MAX_AGE_SECONDS + 60
        )
        fresh = self._make_dir(tmp_root, f"{LOCAL_COPY_PREFIX}new")
        unrelated = self._make_dir(
            tmp_root, "somebody-elses", age_seconds=LOCAL_COPY_MAX_AGE_SECONDS + 60
        )

        with mock.patch(
            "readthedocs.projects.tasks.search.tempfile.gettempdir", return_value=tmp_root
        ):
            _remove_stale_local_copies()

        assert not os.path.exists(stale)
        assert os.path.exists(fresh)
        assert os.path.exists(unrelated)


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
