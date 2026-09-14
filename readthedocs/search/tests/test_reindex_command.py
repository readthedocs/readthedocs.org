from unittest import mock

from django.test import TestCase

from readthedocs.projects.models import HTMLFile
from readthedocs.projects.models import Project
from readthedocs.search.management.commands.reindex_elasticsearch import Command


@mock.patch("readthedocs.search.management.commands.reindex_elasticsearch.search_index_updated")
@mock.patch("readthedocs.search.management.commands.reindex_elasticsearch.switch_es_index")
class TestChangeIndex(TestCase):
    def test_change_index_purges_cached_search_results(self, switch_es_index, search_index_updated):
        Command()._change_index(models=[HTMLFile], timestamp="123")

        switch_es_index.assert_called_once()
        search_index_updated.send.assert_called_once_with(
            sender=Project,
            project=None,
            version=None,
        )

    def test_change_index_projects_only_does_not_purge(self, switch_es_index, search_index_updated):
        Command()._change_index(models=[Project], timestamp="123")

        switch_es_index.assert_called_once()
        search_index_updated.send.assert_not_called()
