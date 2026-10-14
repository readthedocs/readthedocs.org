import pytest
from django_dynamic_fixture import get

from readthedocs.builds.constants import LATEST
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import HTMLFile
from readthedocs.projects.models import Project
from readthedocs.search.documents import PageDocument
from readthedocs.search.faceted_search import PageSearch

from .dummy_data import WRITETHEDOCS_PAGES


@pytest.mark.django_db
@pytest.mark.search
class TestPageSearch:
    @pytest.mark.parametrize("case", ["upper", "lower", "title"])
    def test_search_exact_match(self, client, project, case):
        """Check quoted query match exact phrase with case insensitively

        Making a query with quoted text like ``"foo bar"`` should match
        exactly ``foo bar`` or ``Foo Bar`` etc
        """
        # `Sphinx` word is present both in `kuma` and `docs` files
        # But the phrase `Sphinx uses` is available only in kuma docs.
        # So search with this phrase to check
        query_text = r'"Sphinx uses"'
        cased_query = getattr(query_text, case)
        query = cased_query()

        page_search = PageSearch(query=query)
        results = page_search.execute()

        assert len(results) == 2

        # Both versions have the same exact content.
        # Order of results is not deterministic anymore for some reason,
        # so we use a set to compare the results.
        assert {result["version"] for result in results} == {"stable", "latest"}
        for result in results:
            assert result["project"] == "kuma"
            assert result["path"] == "testdocumentation"

    def test_search_combined_result(self, client, project):
        """Check search result are combined of both `AND` and `OR` operator

        If query is `Foo Bar` then the result should be as following order:

        - Where both `Foo Bar` is present
        - Where `Foo` or `Bar` is present
        """
        query = "Elasticsearch Query"
        page_search = PageSearch(query=query)
        results = page_search.execute()
        assert len(results) == 6

        result_paths_latest = [r.path for r in results if r.version == "latest"]
        result_paths_stable = [r.path for r in results if r.version == "stable"]
        # ``guides/wipe-environment`` page has both ``Elasticsearch Query`` words
        # ``docker`` page has ``Elasticsearch`` word
        # ``installation`` page has ``Query`` word.
        expected_paths = ["guides/wipe-environment", "docker", "installation"]

        assert result_paths_latest == expected_paths
        assert result_paths_stable == expected_paths


@pytest.fixture
def writethedocs(es_index, mock_processed_json, db, settings):
    """
    Index real pages from writethedocs.org, as parsed by our HTML parser.

    The dedicated Slack page has many sections mentioning Slack,
    while each recap has a single short section about it.
    """
    settings.ELASTICSEARCH_DSL_AUTOSYNC = True
    project = get(Project, slug="writethedocs", privacy_level=PUBLIC, versions=[])
    version = project.versions.get(slug=LATEST)
    for basename in WRITETHEDOCS_PAGES:
        html_file = get(
            HTMLFile,
            project=project,
            version=version,
            name=f"{basename}.html",
            path=f"{basename}.html",
            build=1,
        )
        PageDocument().update(html_file)
    return project


@pytest.mark.django_db
@pytest.mark.search
class TestSectionScoring:
    """
    Pages are scored by their best matching section.

    Averaging section scores ranked pages that mention "slack" once
    above the pages about Slack, which have many weaker matches too.
    """

    def _search(self, query):
        page_search = PageSearch(query=query, projects={"writethedocs": LATEST})
        return [result.path for result in page_search.execute()]

    def test_slack_page_ranks_first(self, writethedocs):
        paths = self._search("slack")

        assert paths[0] == "slack"

    def test_slack_pages_rank_above_recaps(self, writethedocs):
        paths = self._search("slack")

        for recap in (
            "conf/au/2017/news/event-recap-feedback",
            "conf/eu/2016/news/thanks-for-coming",
            "conf/portland/2026/news/thanks-recap",
        ):
            assert paths.index("slack") < paths.index(recap)
            assert paths.index("sponsorship/slack") < paths.index(recap)
