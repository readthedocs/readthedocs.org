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
        &lt;h3&gt;<em>XSS</em> exploit&lt;&#x2F;h3&gt;
        """.strip()
        assert results[0].meta.highlight.content[0][:len(expected)] == expected
