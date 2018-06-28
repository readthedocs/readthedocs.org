import pytest
from django.core.urlresolvers import reverse

from readthedocs.search.tests.utils import get_search_query_from_project_file


@pytest.mark.django_db
@pytest.mark.search
class TestPageSearch(object):
    url = reverse('doc_search')

    @pytest.mark.parametrize('data_type', ['content', 'headers', 'title'])
    @pytest.mark.parametrize('page_num', [0, 1])
    def test_search_works(self, api_client, project, data_type, page_num):
        query = get_search_query_from_project_file(project_slug=project.slug, page_num=page_num,
                                                   data_type=data_type)

        version = project.versions.all()[0]
        url = reverse('doc_search')
        resp = api_client.get(url, {'project': project.slug, 'version': version.slug, 'query': query})
        data = resp.data
        assert len(data['results']) == 1

    # @pytest.mark.parametrize('case', ['upper', 'lower', 'title'])
    # def test_file_search_case_insensitive(self, client, project, case):
    #     """Check File search is case insensitive
    #
    #     It tests with uppercase, lowercase and camelcase
    #     """
    #     query_text = get_search_query_from_project_file(project_slug=project.slug)
    #
    #     cased_query = getattr(query_text, case)
    #     query = cased_query()
    #
    #     result, _ = self._get_search_result(url=self.url, client=client,
    #                                         search_params={'q': query, 'type': 'file'})
    #
    #     assert len(result) == 1
    #     # Check the actual text is in the result, not the cased one
    #     assert query_text in result.text()
    #
    # def test_file_search_exact_match(self, client, project):
    #     """Check quoted query match exact phrase
    #
    #     Making a query with quoted text like ``"foo bar"`` should match
    #     exactly ``foo bar`` phrase.
    #     """
    #
    #     # `Github` word is present both in `kuma` and `pipeline` files
    #     # But the phrase Github can is available only in kuma docs.
    #     # So search with this phrase to check
    #     query = r'"GitHub can"'
    #
    #     result, _ = self._get_search_result(url=self.url, client=client,
    #                                         search_params={'q': query, 'type': 'file'})
    #
    #     assert len(result) == 1
    #
    # def test_page_search_not_return_removed_page(self, client, project):
    #     """Check removed page are not in the search index"""
    #     query = get_search_query_from_project_file(project_slug=project.slug)
    #     # Make a query to check it returns result
    #     result, _ = self._get_search_result(url=self.url, client=client,
    #                                         search_params={'q': query, 'type': 'file'})
    #     assert len(result) == 1
    #
    #     # Delete all the HTML files of the project
    #     HTMLFile.objects.filter(project=project).delete()
    #     # Run the query again and this time there should not be any result
    #     result, _ = self._get_search_result(url=self.url, client=client,
    #                                         search_params={'q': query, 'type': 'file'})
    #     assert len(result) == 0
    #
    # def test_file_search_show_projects(self, client, all_projects):
    #     """Test that search result page shows list of projects while searching for files"""
    #
    #     # `Github` word is present both in `kuma` and `pipeline` files
    #     # so search with this phrase
    #     result, page = self._get_search_result(url=self.url, client=client,
    #                                            search_params={'q': 'GitHub', 'type': 'file'})
    #
    #     # There should be 2 search result
    #     assert len(result) == 2
    #
    #     # there should be 2 projects in the left side column
    #     content = page.find('.navigable .project-list')
    #     assert len(content) == 2
    #     text = content.text()
    #
    #     # kuma and pipeline should be there
    #     assert 'kuma' and 'pipeline' in text
    #
    # def test_file_search_filter_by_project(self, client):
    #     """Test that search result are filtered according to project"""
    #
    #     # `Github` word is present both in `kuma` and `pipeline` files
    #     # so search with this phrase but filter through `kuma` project
    #     search_params = {'q': 'GitHub', 'type': 'file', 'project': 'kuma'}
    #     result, page = self._get_search_result(url=self.url, client=client,
    #                                            search_params=search_params)
    #
    #     # There should be 1 search result as we have filtered
    #     assert len(result) == 1
    #     content = page.find('.navigable .project-list')
    #
    #     # kuma should should be there only
    #     assert 'kuma' in result.text()
    #     assert 'pipeline' not in result.text()
    #
    #     # But there should be 2 projects in the left side column
    #     # as the query is present in both projects
    #     content = page.find('.navigable .project-list')
    #     if len(content) != 2:
    #         pytest.xfail("failing because currently all projects are not showing in project list")
    #     else:
    #         assert 'kuma' and 'pipeline' in content.text()
    #
    # @pytest.mark.xfail(reason="Versions are not showing correctly! Fixme while rewrite!")
    # def test_file_search_show_versions(self, client, all_projects, es_index, settings):
    #     # override the settings to index all versions
    #     settings.INDEX_ONLY_LATEST = False
    #
    #     project = all_projects[0]
    #     # Create some versions of the project
    #     versions = [G(Version, project=project) for _ in range(3)]
    #
    #     query = get_search_query_from_project_file(project_slug=project.slug)
    #
    #     result, page = self._get_search_result(url=self.url, client=client,
    #                                            search_params={'q': query, 'type': 'file'})
    #
    #     # There should be only one result because by default
    #     # only latest version result should be there
    #     assert len(result) == 1
    #
    #     content = page.find('.navigable .version-list')
    #     # There should be total 4 versions
    #     # one is latest, and other 3 that we created above
    #     assert len(content) == 4
    #
    #     project_versions = [v.slug for v in versions] + [LATEST]
    #     content_versions = []
    #     for element in content:
    #         text = element.text_content()
    #         # strip and split to keep the version slug only
    #         slug = text.strip().split('\n')[0]
    #         content_versions.append(slug)
    #
    #     assert sorted(project_versions) == sorted(content_versions)
    #
    # def test_file_search_subprojects(self, client, all_projects, es_index):
    #     """File search should return results from subprojects also"""
    #     project = all_projects[0]
    #     subproject = all_projects[1]
    #     # Add another project as subproject of the project
    #     project.add_subproject(subproject)
    #
    #     # Now search with subproject content but explicitly filter by the parent project
    #     query = get_search_query_from_project_file(project_slug=subproject.slug)
    #     search_params = {'q': query, 'type': 'file', 'project': project.slug}
    #     result, page = self._get_search_result(url=self.url, client=client,
    #                                            search_params=search_params)
    #
    #     assert len(result) == 1