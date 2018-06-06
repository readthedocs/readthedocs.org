import pytest
from django.core.management import call_command


class SearchTestMixin:
    def _reindex_elasticsearch(self, es_index):
        call_command('reindex_elasticsearch')
        es_index.refresh_index()

    @pytest.fixture(autouse=True)
    def elastic_index(self, mock_parse_json, all_projects, es_index):
        self._reindex_elasticsearch(es_index=es_index)
