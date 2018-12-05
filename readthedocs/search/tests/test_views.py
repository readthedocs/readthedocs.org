# -*- coding: utf-8 -*-

import pytest
from django.core.management import call_command
from django.core.urlresolvers import reverse_lazy
from django_dynamic_fixture import G
from pyquery import PyQuery as pq

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.search.tests.utils import get_search_query_from_project_file


@pytest.mark.django_db
@pytest.mark.search
class TestElasticSearch(object):

    url = reverse_lazy('search')

    def _reindex_elasticsearch(self, es_index):
        call_command('reindex_elasticsearch')
        es_index.refresh_index()

    def _get_search_result(self, url, client, search_params):
        resp = client.get(url, search_params)
        assert resp.status_code == 200

        page = pq(resp.content)
        result = page.find('.module-list-wrapper .module-item-title')
        return result, page

    @pytest.fixture(autouse=True)
    def elastic_index(self, mock_parse_json, all_projects, es_index):
        self._reindex_elasticsearch(es_index=es_index)

    def test_search_by_project_name(self, client, project):
        result, _ = self._get_search_result(url=self.url, client=client,
                                            search_params={'q': project.name})

        assert project.name.encode('utf-8') in result.text().encode('utf-8')

    def test_search_project_show_languages(self, client, project, es_index):
        """Test that searching project should show all available languages"""
        # Create a project in bn and add it as a translation
        G(Project, language='bn', name=project.name)
        self._reindex_elasticsearch(es_index=es_index)

        result, page = self._get_search_result(url=self.url, client=client,
                                               search_params={'q': project.name})

        content = page.find('.navigable .language-list')
        # There should be 2 languages
        assert len(content) == 2
        assert 'bn' in content.text()

    def test_search_project_filter_language(self, client, project, es_index):
        """Test that searching project filtered according to language"""
        # Create a project in bn and add it as a translation
        translate = G(Project, language='bn', name=project.name)
        self._reindex_elasticsearch(es_index=es_index)
        search_params = {'q': project.name, 'language': 'bn'}

        result, page = self._get_search_result(url=self.url, client=client,
                                               search_params=search_params)

        # There should be only 1 result
        assert len(result) == 1

        content = page.find('.navigable .language-list')
        # There should be 1 languages
        assert len(content) == 1
        assert 'bn' in content.text()

    @pytest.mark.parametrize('data_type', ['content', 'headers', 'title'])
    @pytest.mark.parametrize('page_num', [0, 1])
    def test_search_by_file_content(self, client, project, data_type, page_num):
        query = get_search_query_from_project_file(project_slug=project.slug, page_num=page_num,
                                                   data_type=data_type)

        result, _ = self._get_search_result(url=self.url, client=client,
                                            search_params={'q': query, 'type': 'file'})
        assert len(result) == 1

    def test_file_search_show_projects(self, client):
        """Test that search result page shows list of projects while searching for files"""

        # `Github` word is present both in `kuma` and `pipeline` files
        # so search with this phrase
        result, page = self._get_search_result(url=self.url, client=client,
                                               search_params={'q': 'GitHub', 'type': 'file'})

        # There should be 2 search result
        assert len(result) == 2

        # there should be 2 projects in the left side column
        content = page.find('.navigable .project-list')
        assert len(content) == 2
        text = content.text()

        # kuma and pipeline should be there
        assert 'kuma' and 'pipeline' in text

    def test_file_search_filter_by_project(self, client):
        """Test that search result are filtered according to project"""

        # `Github` word is present both in `kuma` and `pipeline` files
        # so search with this phrase but filter through `kuma` project
        search_params = {'q': 'GitHub', 'type': 'file', 'project': 'kuma'}
        result, page = self._get_search_result(url=self.url, client=client,
                                               search_params=search_params)

        # There should be 1 search result as we have filtered
        assert len(result) == 1
        content = page.find('.navigable .project-list')

        # kuma should should be there only
        assert 'kuma' in result.text()
        assert 'pipeline' not in result.text()

        # But there should be 2 projects in the left side column
        # as the query is present in both projects
        content = page.find('.navigable .project-list')
        if len(content) != 2:
            pytest.xfail("failing because currently all projects are not showing in project list")
        else:
            assert 'kuma' and 'pipeline' in content.text()

    @pytest.mark.xfail(reason="Versions are not showing correctly! Fixme while rewrite!")
    def test_file_search_show_versions(self, client, all_projects, es_index, settings):
        # override the settings to index all versions
        settings.INDEX_ONLY_LATEST = False

        project = all_projects[0]
        # Create some versions of the project
        versions = [G(Version, project=project) for _ in range(3)]
        self._reindex_elasticsearch(es_index=es_index)

        query = get_search_query_from_project_file(project_slug=project.slug)

        result, page = self._get_search_result(url=self.url, client=client,
                                               search_params={'q': query, 'type': 'file'})

        # There should be only one result because by default
        # only latest version result should be there
        assert len(result) == 1

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
        """File search should return results from subprojects also"""
        project = all_projects[0]
        subproject = all_projects[1]
        # Add another project as subproject of the project
        project.add_subproject(subproject)
        self._reindex_elasticsearch(es_index=es_index)

        # Now search with subproject content but explicitly filter by the parent project
        query = get_search_query_from_project_file(project_slug=subproject.slug)
        search_params = {'q': query, 'type': 'file', 'project': project.slug}
        result, page = self._get_search_result(url=self.url, client=client,
                                               search_params=search_params)

        assert len(result) == 1
