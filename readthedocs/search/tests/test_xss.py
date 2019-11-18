import pytest

from readthedocs.search.documents import PageDocument


@pytest.mark.django_db
@pytest.mark.search
class TestXSS:

    def test_facted_page_xss(self, client, project):
        query = 'XSS'
        page_search = PageDocument.faceted_search(query=query, user='')
        results = page_search.execute()
        expected = """
        &lt;h3&gt;<span>XSS</span> exploit&lt;&#x2F;h3&gt;
        """.strip()

        hits = results.hits.hits
        assert len(hits) == 2
        assert hits[0]['_source']['version'] == 'stable'
        assert hits[1]['_source']['version'] == 'latest'

        for hit in hits:
            inner_hits = hit['inner_hits']

            domain_hits = inner_hits['domains']['hits']['hits']
            assert len(domain_hits) == 0  # there shouldn't be any results from domains

            section_hits = inner_hits['sections']['hits']['hits']
            assert len(section_hits) == 1

            section_content_highlight = section_hits[0]['highlight']['sections.content']
            assert len(section_content_highlight) == 1

            assert expected in section_content_highlight[0]
