# -*- coding: utf-8 -*-

import re

import pytest
from django.urls import reverse
from django_dynamic_fixture import G

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search.tests.utils import (
    get_search_query_from_project_file,
    DATA_TYPES_VALUES,
)


@pytest.mark.django_db
@pytest.mark.search
class TestProjectSearch:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.url =  reverse('search')

    def _get_search_result(self, url, client, search_params):
        resp = client.get(url, search_params)
        assert resp.status_code == 200

        results = resp.context['results']
        facets = resp.context['facets']

        return results, facets

    def test_search_by_project_name(self, client, project, all_projects):
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': project.name },
        )

        assert len(results) == 1
        assert project.name.encode('utf-8') in results[0].name.encode('utf-8')
        for proj in all_projects[1:]:
            assert proj.name.encode('utf-8') not in results[0].name.encode('utf-8')

    def test_search_project_have_correct_language_facets(self, client, project):
        """Test that searching project should have correct language facets in the results"""
        # Create a project in bn and add it as a translation
        G(Project, language='bn', name=project.name)

        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': project.name },
        )

        lang_facets = facets['language']
        lang_facets_str = [facet[0] for facet in lang_facets]
        # There should be 2 languages
        assert len(lang_facets) == 2
        assert sorted(lang_facets_str) == sorted(['en', 'bn'])
        for facet in lang_facets:
            assert facet[2] == False  # because none of the facets are applied

    def test_search_project_filter_language(self, client, project):
        """Test that searching project filtered according to language."""
        # Create a project in bn and add it as a translation
        translate = G(Project, language='bn', name=project.name)
        search_params = { 'q': project.name, 'language': 'bn' }

        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )

        # There should be only 1 result
        assert len(results) == 1

        lang_facets = facets['language']
        lang_facets_str = [facet[0] for facet in lang_facets]

        # There should be 2 languages because both `en` and `bn` should show there
        assert len(lang_facets) == 2
        assert sorted(lang_facets_str) == sorted(['en', 'bn'])


@pytest.mark.django_db
@pytest.mark.search
class TestPageSearch:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.url =  reverse('search')

    def _get_search_result(self, url, client, search_params):
        resp = client.get(url, search_params)
        assert resp.status_code == 200

        results = resp.context['results']
        facets = resp.context['facets']

        return results, facets

    def _get_highlight(self, result, data_type):
        # if query is from page title,
        # highlighted title is present in 'result.meta.highlight.title'
        if data_type == 'title':
            highlight = result.meta.highlight.title

        # if result is not from page title,
        # then results and highlighted results are present inside 'inner_hits'
        else:
            inner_hits = result.meta.inner_hits
            assert len(inner_hits) >= 1

            # checking first inner_hit
            inner_hit_0 = inner_hits[0]
            expected_type = data_type.split('.')[0]  # can be either 'sections' or 'domains'
            assert inner_hit_0['type'] == expected_type
            highlight = inner_hit_0['highlight'][data_type]

        return highlight

    def _get_highlighted_words(self, string):
        highlighted_words = re.findall(
            '<span>(.*?)</span>',
            string
        )
        return highlighted_words

    @pytest.mark.parametrize('data_type', DATA_TYPES_VALUES)
    @pytest.mark.parametrize('page_num', [0, 1])
    def test_file_search(self, client, project, data_type, page_num):
        query = get_search_query_from_project_file(
            project_slug=project.slug,
            page_num=page_num,
            data_type=data_type
        )
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': query, 'type': 'file' }
        )
        assert len(results) >= 1

        # checking first result
        result_0 = results[0]
        highlight = self._get_highlight(result_0, data_type)
        assert len(highlight) == 1

        highlighted_words = self._get_highlighted_words(highlight[0])
        assert len(highlighted_words) >= 1
        for word in highlighted_words:
            # Make it lower because our search is case insensitive
            assert word.lower() in query.lower()

    def test_file_search_have_correct_role_name_facets(self, client):
        """Test that searching files should result all role_names."""

        # searching for 'celery' to test that
        # correct role_names are displayed
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': 'celery', 'type': 'file' }
        )
        assert len(results) >= 1
        role_name_facets = facets['role_name']
        role_name_facets_str = [facet[0] for facet in role_name_facets]
        expected_role_names = ['py:class', 'py:function', 'py:method']
        assert sorted(expected_role_names) == sorted(role_name_facets_str)
        for facet in role_name_facets:
            assert facet[2] == False  # because none of the facets are applied

    def test_file_search_filter_role_name(self, client):
        """Test that searching files filtered according to role_names."""

        search_params = { 'q': 'celery', 'type': 'file' }
        # searching without the filter
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params
        )
        assert len(results) >= 2  # there are > 1 results without the filter
        role_name_facets = facets['role_name']
        for facet in role_name_facets:
            assert facet[2] == False  # because none of the facets are applied

        confval_facet = 'py:class'
        # checking if 'py:class' facet is present in results
        assert confval_facet in [facet[0] for facet in role_name_facets]

        # filtering with role_name=py:class
        search_params['role_name'] = confval_facet
        new_results, new_facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params
        )
        new_role_names_facets = new_facets['role_name']
        # there is only one result with role_name='py:class'
        # in `signals` page
        assert len(new_results) == 1
        first_result = new_results[0]  # first result
        inner_hits = first_result.meta.inner_hits  # inner_hits of first results
        assert len(inner_hits) >= 1
        inner_hit_0 = inner_hits[0]  # first inner_hit
        assert inner_hit_0.type == 'domains'
        assert inner_hit_0.source.role_name == confval_facet

        for facet in new_role_names_facets:
            if facet[0] == confval_facet:
                assert facet[2] == True  # because 'std:confval' filter is active
            else:
                assert facet[2] == False

    @pytest.mark.parametrize('data_type', DATA_TYPES_VALUES)
    @pytest.mark.parametrize('case', ['upper', 'lower', 'title'])
    def test_file_search_case_insensitive(self, client, project, case, data_type):
        """
        Check File search is case insensitive.

        It tests with uppercase, lowercase and camelcase.
        """
        query_text = get_search_query_from_project_file(
            project_slug=project.slug,
            data_type=data_type
        )
        cased_query = getattr(query_text, case)
        query = cased_query()

        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': query, 'type': 'file' }
        )
        assert len(results) >= 1

        first_result = results[0]
        highlight = self._get_highlight(first_result, data_type)
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
            url=self.url,
            client=client,
            search_params={ 'q': query, 'type': 'file' })

        # there must be only 1 result
        # because the phrase is present in
        # only one project
        assert len(results) == 1
        assert results[0].project == 'kuma'
        assert results[0].path == 'testdocumentation'

        inner_hits = results[0].meta.inner_hits
        assert len(inner_hits) == 1
        assert inner_hits[0].type == 'sections'
        highlight = self._get_highlight(results[0], 'sections.content')
        assert len(highlight) == 1
        highlighted_words = self._get_highlighted_words(highlight[0])
        assert len(highlighted_words) >= 1
        for word in highlighted_words:
            assert word.lower() in query.lower()

    def test_file_search_have_correct_project_facets(self, client, all_projects):
        """Test that file search have correct project facets in results"""

        # `environment` word is present both in `kuma` and `docs` files
        # so search with this phrase
        query = 'environment'
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': query, 'type': 'file' },
        )
        # There should be 2 search result
        assert len(results) == 2
        project_facets = facets['project']
        project_facets_str = [facet[0] for facet in project_facets]
        assert len(project_facets_str) == 2

        # kuma and pipeline should be there
        assert sorted(project_facets_str) == sorted(['kuma', 'docs'])

    def test_file_search_filter_by_project(self, client):
        """Test that search result are filtered according to project."""

        # `environment` word is present both in `kuma` and `docs` files
        # so search with this phrase but filter through `kuma` project
        search_params = {
            'q': 'environment',
            'type': 'file',
            'project': 'kuma'
        }
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        project_facets = facets['project']
        resulted_project_facets = [ facet[0] for facet in project_facets ]

        # There should be 1 search result as we have filtered
        assert len(results) == 1
        # kuma should should be there only
        assert 'kuma' == results[0].project

        # But there should be 2 projects in the project facets
        # as the query is present in both projects
        assert sorted(resulted_project_facets) == sorted(['kuma', 'docs'])

    @pytest.mark.xfail(reason='Versions are not showing correctly! Fixme while rewrite!')
    def test_file_search_show_versions(self, client, all_projects, es_index, settings):
        # override the settings to index all versions
        settings.INDEX_ONLY_LATEST = False

        project = all_projects[0]
        # Create some versions of the project
        versions = [G(Version, project=project) for _ in range(3)]
        query = get_search_query_from_project_file(project_slug=project.slug)
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': query, 'type': 'file' },
        )

        # Results can be from other projects also
        assert len(results) >= 1

        version_facets = facets['version']
        version_facets_str = [facet[0] for facet in version_facets]
        # There should be total 4 versions
        # one is latest, and other 3 that we created above
        assert len(version_facets) == 4

        project_versions = [v.slug for v in versions] + [LATEST]
        assert sorted(project_versions) == sorted(resulted_version_facets)

    def test_file_search_subprojects(self, client, all_projects, es_index):
        """
        TODO: File search should return results from subprojects also.

        This is currently disabled because the UX around it is weird.
        You filter by a project, and get results for multiple.
        """
        project = all_projects[0]
        subproject = all_projects[1]
        # Add another project as subproject of the project
        project.add_subproject(subproject)

        # Now search with subproject content but explicitly filter by the parent project
        query = get_search_query_from_project_file(project_slug=subproject.slug)
        search_params = {
            'q': query,
            'type': 'file',
            'project': project.slug,
        }
        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        assert len(results) == 0
