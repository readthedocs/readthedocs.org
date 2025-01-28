import re

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.search.tests.utils import (
    DATA_TYPES_VALUES,
    get_search_query_from_project_file,
)


@pytest.mark.django_db
@pytest.mark.search
class TestProjectSearch:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("search")

    def _get_search_result(self, url, client, search_params):
        resp = client.get(url, search_params)
        assert resp.status_code == 200

        results = resp.context["results"]
        facets = resp.context["facets"]

        return results, facets

    def test_search_by_project_name(self, client, project, all_projects):
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params={"q": project.name, "type": "project"},
        )

        assert len(results) == 1
        assert project.name == results[0]["name"]
        for proj in all_projects[1:]:
            assert proj.name != results[0]["name"]

    def test_search_project_have_correct_language_facets(self, client, project):
        """Test that searching project should have correct language facets in the results"""
        # Create a project in bn and add it as a translation
        get(Project, language="bn", name=project.name)

        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params={"q": project.name, "type": "project"},
        )

        lang_facets = facets["language"]
        lang_facets_str = [facet[0] for facet in lang_facets]
        # There should be 2 languages
        assert len(lang_facets) == 2
        assert sorted(lang_facets_str) == sorted(["en", "bn"])
        for facet in lang_facets:
            assert facet[2] == False  # because none of the facets are applied

    def test_search_project_filter_language(self, client, project):
        """Test that searching project filtered according to language."""
        # Create a project in bn and add it as a translation
        translate = get(Project, language="bn", name=project.name)
        search_params = {"q": project.name, "language": "bn", "type": "project"}

        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )

        # There should be only 1 result
        assert len(results) == 1

        lang_facets = facets["language"]
        lang_facets_str = [facet[0] for facet in lang_facets]

        # There should be 2 languages because both `en` and `bn` should show there
        assert len(lang_facets) == 2
        assert sorted(lang_facets_str) == sorted(["en", "bn"])

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_search_only_projects_owned_by_the_user(self, client, all_projects):
        project = Project.objects.get(slug="docs")
        user = get(User)
        user.projects.add(project)
        client.force_login(user)
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params={
                # Search for all projects.
                "q": " ".join(project.slug for project in all_projects),
                "type": "project",
            },
        )
        assert len(results) > 0

        other_projects = [
            project.slug for project in all_projects if project.slug != "docs"
        ]

        for result in results:
            assert result["name"] == "docs"
            assert result["name"] not in other_projects

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_search_no_owned_projects(self, client, all_projects):
        user = get(User)
        assert user.projects.all().count() == 0
        client.force_login(user)
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params={
                # Search for all projects.
                "q": " ".join(project.slug for project in all_projects),
                "type": "project",
            },
        )
        assert len(results) == 0

    def test_search_empty_query(self, client):
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params={"q": "", "type": "project"},
        )
        assert results == []
        assert facets == {}


@pytest.mark.django_db
@pytest.mark.search
@pytest.mark.usefixtures("all_projects")
class TestPageSearch:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("search")

    def _get_search_result(self, url, client, search_params):
        resp = client.get(url, search_params)
        assert resp.status_code == 200

        results = resp.context["results"]
        facets = resp.context["facets"]

        return results, facets

    def _get_highlight(self, result, field, type=None):
        # if query is from page title,
        # highlighted title is present in 'result.meta.highlight.title'
        if not type and field == "title":
            highlight = result["highlights"]["title"]

        # if result is not from page title,
        # then results and highlighted results are present inside 'blocks'
        else:
            blocks = result["blocks"]
            assert len(blocks) >= 1

            # checking first inner_hit
            inner_hit_0 = blocks[0]
            assert inner_hit_0["type"] == type
            highlight = inner_hit_0["highlights"][field]

        return highlight

    def _get_highlighted_words(self, string):
        highlighted_words = re.findall("<span>(.*?)</span>", string)
        return highlighted_words

    @pytest.mark.parametrize("data_type", DATA_TYPES_VALUES)
    @pytest.mark.parametrize("page_num", [0, 1])
    def test_file_search(self, client, project, data_type, page_num):
        data_type = data_type.split(".")
        type, field = None, None
        if len(data_type) < 2:
            field = data_type[0]
        else:
            type, field = data_type
        query = get_search_query_from_project_file(
            project_slug=project.slug,
            page_num=page_num,
            type=type,
            field=field,
        )
        results, _ = self._get_search_result(
            url=self.url, client=client, search_params={"q": query, "type": "file"}
        )
        assert len(results) >= 1

        # checking first result
        result_0 = results[0]
        highlight = self._get_highlight(result_0, field, type)
        assert len(highlight) == 1

        highlighted_words = self._get_highlighted_words(highlight[0])
        assert len(highlighted_words) >= 1
        for word in highlighted_words:
            # Make it lower because our search is case insensitive
            assert word.lower() in query.lower()

    @pytest.mark.parametrize("data_type", DATA_TYPES_VALUES)
    @pytest.mark.parametrize("case", ["upper", "lower", "title"])
    def test_file_search_case_insensitive(self, client, project, case, data_type):
        """
        Check File search is case insensitive.

        It tests with uppercase, lowercase and camelcase.
        """
        type, field = None, None
        data_type = data_type.split(".")
        if len(data_type) < 2:
            field = data_type[0]
        else:
            type, field = data_type
        query_text = get_search_query_from_project_file(
            project_slug=project.slug,
            type=type,
            field=field,
        )
        cased_query = getattr(query_text, case)
        query = cased_query()

        results, _ = self._get_search_result(
            url=self.url, client=client, search_params={"q": query, "type": "file"}
        )
        assert len(results) >= 1

        first_result = results[0]
        highlight = self._get_highlight(first_result, field, type)
        assert len(highlight) == 1
        highlighted_words = self._get_highlighted_words(highlight[0])
        assert len(highlighted_words) >= 1
        for word in highlighted_words:
            assert word.lower() in query.lower()

    def test_file_search_exact_match(self, client, project):
        """
        Check quoted query match exact phrase.

        Making a query with quoted text like ``"foo bar"`` should match exactly
        ``foo bar`` phrase.
        """

        # `Sphinx` word is present both in `kuma` and `docs` files
        # But the phrase `Sphinx uses` is present only in `kuma` docs.
        # So search with this phrase to check
        query = r'"Sphinx uses"'
        results, _ = self._get_search_result(
            url=self.url, client=client, search_params={"q": query, "type": "file"}
        )

        # There are two results,
        # one from each version of the "kuma" project.
        assert len(results) == 2
        # Both versions have the same exact content.
        # Order of results is not deterministic anymore for some reason,
        # so we use a set to compare the results.
        assert {result["version"]["slug"] for result in results} == {"stable", "latest"}
        for result in results:
            assert result["project"] == {"alias": None, "slug": "kuma"}
            assert result["domain"] == "http://kuma.readthedocs.io"
            assert result["path"].endswith("/documentation.html")

        blocks = results[0]["blocks"]
        assert len(blocks) == 1
        assert blocks[0]["type"] == "section"
        highlight = self._get_highlight(results[0], "content", "section")
        assert len(highlight) == 1
        highlighted_words = self._get_highlighted_words(highlight[0])
        assert len(highlighted_words) >= 1
        for word in highlighted_words:
            assert word.lower() in query.lower()

    def test_file_search_filter_by_project(self, client):
        """Test that search result are filtered according to project."""

        # `environment` word is present both in `kuma` and `docs` files
        # so search with this phrase but filter through `kuma` project
        search_params = {
            "q": "project:kuma environment",
            "type": "file",
        }
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        project_facets = facets["project"]
        resulted_project_facets = [facet[0] for facet in project_facets]

        # There should be 1 search result as we have filtered
        assert len(results) == 1
        # kuma should should be there only
        assert {"alias": None, "slug": "kuma"} == results[0]["project"]

        # The projects we search is the only one included in the final results.
        assert resulted_project_facets == ["kuma"]

    @pytest.mark.xfail(
        reason="Versions are not showing correctly! Fixme while rewrite!"
    )
    def test_file_search_show_versions(self, client, all_projects, es_index, settings):
        project = all_projects[0]
        # Create some versions of the project
        versions = [get(Version, project=project) for _ in range(3)]
        query = get_search_query_from_project_file(project_slug=project.slug)
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params={"q": query, "type": "file"},
        )

        # Results can be from other projects also
        assert len(results) >= 1

        version_facets = facets["version"]
        version_facets_str = [facet[0] for facet in version_facets]
        # There should be total 4 versions
        # one is latest, and other 3 that we created above
        assert len(version_facets) == 4

        project_versions = [v.slug for v in versions] + [LATEST]
        assert sorted(project_versions) == sorted(version_facets_str)

    def test_file_search_subprojects(self, client, all_projects, es_index):
        project = all_projects[0]
        subproject = all_projects[1]
        # Add another project as subproject of the project
        project.add_subproject(subproject, alias="subproject")

        # Now search with subproject content but explicitly filter by the parent project
        query = get_search_query_from_project_file(project_slug=subproject.slug)
        search_params = {
            "q": f"subprojects:{project.slug} {query}",
            "type": "file",
        }
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        assert len(results) == 1
        assert results[0]["project"] == {"alias": "subproject", "slug": subproject.slug}

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_search_only_projects_owned_by_the_user(self, client, all_projects):
        project = Project.objects.get(slug="docs")
        user = get(User)
        user.projects.add(project)
        client.force_login(user)
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            # Search for the most common english word.
            search_params={"q": "the", "type": "file"},
        )
        assert len(results) > 0

        for result in results:
            assert result["project"] == {"alias": None, "slug": "docs"}

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_search_no_owned_projects(self, client, all_projects):
        user = get(User)
        assert user.projects.all().count() == 0
        client.force_login(user)
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            # Search for the most common english word.
            search_params={"q": "the", "type": "file"},
        )
        assert len(results) == 0
