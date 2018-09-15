import pytest

from readthedocs.search.documents import PageDocument


class TestFileSearch(object):

    @pytest.mark.parametrize('case', ['upper', 'lower', 'title'])
    def test_search_exact_match(self, client, project, case):
        """Check quoted query match exact phrase with case insensitively

        Making a query with quoted text like ``"foo bar"`` should match
        exactly ``foo bar`` or ``Foo Bar`` etc
        """
        # `Github` word is present both in `kuma` and `pipeline` files
        # But the phrase Github can is available only in kuma docs.
        # So search with this phrase to check
        query_text = r'"GitHub can"'
        cased_query = getattr(query_text, case)
        query = cased_query()

        page_search = PageDocument.faceted_search(query=query)
        results = page_search.execute()

        assert len(results) == 1
        assert results[0]['project'] == 'kuma'
        assert results[0]['path'] == 'documentation'

    def test_search_combined_result(self, client, project):
        """Check search result are combined of both `AND` and `OR` operator

        If query is `Foo Bar` then the result should be as following order:

        - Where both `Foo Bar` is present
        - Where `Foo` or `Bar` is present
        """
        query = 'Official Support'
        page_search = PageDocument.faceted_search(query=query)
        results = page_search.execute()
        assert len(results) == 3

        result_paths = [r.path for r in results]
        # ``open-source-philosophy`` page has both ``Official Support`` words
        # ``docker`` page has ``Support`` word
        # ``installation`` page has ``Official`` word
        expected_paths = ['open-source-philosophy', 'docker', 'installation']

        assert result_paths == expected_paths
