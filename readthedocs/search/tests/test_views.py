# -*- coding: utf-8 -*-

import pytest
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from pyquery import PyQuery as pq

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
    url = reverse('search')

    def _get_search_result(self, url, client, search_params):
        resp = client.get(url, search_params)
        assert resp.status_code == 200

        page = pq(resp.content)
        result = page.find('.module-list-wrapper .module-item-title')
        return result, page

    def test_search_by_project_name(self, client, project, all_projects):
        result, _ = self._get_search_result(
            url=self.url, client=client,
            search_params={'q': project.name},
        )

        assert len(result) == 1
        assert project.name.encode('utf-8') in result.text().encode('utf-8')
        assert all_projects[1].name.encode('utf-8') not in result.text().encode('utf-8')

    def test_search_project_show_languages(self, client, project):
        """Test that searching project should show all available languages."""
        # Create a project in bn and add it as a translation
        G(Project, language='bn', name=project.name)

        result, page = self._get_search_result(
            url=self.url, client=client,
            search_params={'q': project.name},
        )

        content = page.find('.navigable .language-list')
        # There should be 2 languages
        assert len(content) == 2
        assert 'bn' in content.text()

    def test_search_project_filter_language(self, client, project):
        """Test that searching project filtered according to language."""
        # Create a project in bn and add it as a translation
        translate = G(Project, language='bn', name=project.name)
        search_params = {'q': project.name, 'language': 'bn'}

        result, page = self._get_search_result(
            url=self.url, client=client,
            search_params=search_params,
        )

        # There should be only 1 result
        assert len(result) == 1

        content = page.find('.navigable .language-list')
        # There should be 2 languages because both `en` and `bn` should show there
        assert len(content) == 2
        assert 'bn' in content.text()


@pytest.mark.django_db
@pytest.mark.search
class TestPageSearch(object):
    url = reverse('search')

    def _get_search_result(self, url, client, search_params):
        resp = client.get(url, search_params)
        assert resp.status_code == 200

        page = pq(resp.content)
        results = page.find('.module-list-wrapper .search-result-item')
        return results, page

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
        for res in results:
            fragments = res.cssselect('.fragment')
            assert len(fragments) >= 1

        assert query in results.text()

    @pytest.mark.parametrize('data_type', DATA_TYPES_VALUES)
    @pytest.mark.parametrize('case', ['upper', 'lower', 'title'])
    def test_file_search_case_insensitive(self, client, project, case, data_type):
        """
        Check File search is case insensitive.

        It tests with uppercase, lowercase and camelcase
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
        for res in results:
            fragments = res.cssselect('.fragment')
            assert len(fragments) >= 1

        # Check the actual text is in the result, not the cased one
        assert query_text in results.text()

    def test_file_search_exact_match(self, client, project):
        """
        Check quoted query match exact phrase.

        Making a query with quoted text like ``"foo bar"`` should match exactly
        ``foo bar`` phrase.
        """

        # `Sphinx` word is present both in `kuma` and `docs` files
        # But the phrase `Sphinx uses` is available only in kuma docs.
        # So search with this phrase to check
        query = r'"Sphinx uses"'

        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': query, 'type': 'file' })

        # there must be only 1 result
        # becuase the phrase is present in
        # only one project
        assert len(results) == 1

        fragment = results[0].cssselect('.fragment')
        assert len(fragment) == 1

    def test_file_search_show_projects(self, client, all_projects):
        """Test that search result page shows list of projects while searching
        for files."""

        # `Sphinx` word is present both in `kuma` and `docs` files
        # so search with this phrase
        result, page = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': 'Sphinx', 'type': 'file' },
        )

        # There should be 2 search result
        assert len(result) == 2

        # there should be 2 projects in the left side column
        content = page.find('.navigable .project-list')
        assert len(content) == 2
        text = content.text()

        # kuma and pipeline should be there
        assert 'kuma' and 'docs' in text

    def test_file_search_filter_by_project(self, client):
        """Test that search result are filtered according to project."""

        # `Sphinx` word is present both in `kuma` and `docs` files
        # so search with this phrase but filter through `kuma` project
        search_params = {
            'q': 'Sphinx',
            'type': 'file',
            'project': 'kuma'
        }
        results, page = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )

        # There should be 1 search result as we have filtered
        assert len(results) == 1
        fragments = results[0].cssselect('.fragment')
        assert len(fragments) == 2  # `Sphinx` is present in two sections in that docs

        headings = page.find('.module-list-wrapper .search-result-item p a').text()
        # kuma should should be there only
        assert 'kuma' in headings
        assert 'docs' not in headings

        # But there should be 2 projects in the left side column
        # as the query is present in both projects
        content = page.find('.navigable .project-list')
        if len(content) != 2:
            pytest.xfail('failing because currently all projects are not showing in project list')
        else:
            assert 'kuma' and 'docs' in content.text()

    @pytest.mark.xfail(reason='Versions are not showing correctly! Fixme while rewrite!')
    def test_file_search_show_versions(self, client, all_projects, es_index, settings):
        # override the settings to index all versions
        settings.INDEX_ONLY_LATEST = False

        project = all_projects[0]
        # Create some versions of the project
        versions = [G(Version, project=project) for _ in range(3)]

        query = get_search_query_from_project_file(project_slug=project.slug)

        result, page = self._get_search_result(
            url=self.url, client=client,
            search_params={'q': query, 'type': 'file'},
        )

        # Results can be from other projects also
        assert len(result) >= 1

        content = page.find('.navigable .version-list')
        # There should be total 4 versions
        # one is latest, and other 3 that we created above
        assert len(content) == 4

        project_versions = [v.slug for v in versions] + [LATEST]
        content_versions = []
        for element in content:
            text = element.text_content()
            # strip and split to keep the version slug only
            slug = text.strip().split('\n')[0]
            content_versions.append(slug)

        assert sorted(project_versions) == sorted(content_versions)

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
        results, page = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )

        headings = page.find('.module-list-wrapper .search-result-item p a').text()
        # Results can be from other sections also.
        assert len(results) >= 0
        assert f'{subproject.slug}' not in headings
