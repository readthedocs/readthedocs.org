import pytest

from readthedocs.search.faceted_search import PageSearch


@pytest.mark.django_db
@pytest.mark.search
class TestXSS:
    def test_facted_page_xss(self, all_projects):
        query = '"XSS"'
        page_search = PageSearch(query=query, projects={"docs": "latest"})
        results = page_search.execute()
        expected = """
        &lt;h3&gt;<span>XSS</span> exploit&lt;&#x2F;h3&gt;
        """.strip()

        hits = results.hits.hits
        assert len(hits) == 1
        assert hits[0]["_source"]["version"] == "latest"

        inner_hits = hits[0]["inner_hits"]

        section_hits = inner_hits["sections"]["hits"]["hits"]
        assert len(section_hits) == 1

        section_content_highlight = section_hits[0]["highlight"]["sections.content"]
        assert len(section_content_highlight) == 1

        assert expected in section_content_highlight[0]
