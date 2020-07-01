import re
from unittest import mock

import pytest
from django.urls import reverse
from django_dynamic_fixture import G

from readthedocs.builds.models import Version
from readthedocs.projects.constants import (
    MKDOCS,
    MKDOCS_HTML,
    PUBLIC,
    SPHINX,
    SPHINX_HTMLDIR,
    SPHINX_SINGLEHTML,
)
from readthedocs.projects.models import HTMLFile, Project, Feature
from readthedocs.search.api import PageSearchAPIView
from readthedocs.search.documents import PageDocument
from readthedocs.search.tests.utils import (
    DOMAIN_FIELDS,
    SECTION_FIELDS,
    get_search_query_from_project_file,
)

OLD_TYPES = {
    'domain': 'domains',
    'section': 'sections',
}
OLD_FIELDS = {
    'docstring': 'docstrings',
}


@pytest.mark.django_db
@pytest.mark.search
@pytest.mark.usefixtures("all_projects")
class BaseTestDocumentSearch:

    def setup_method(self, method):
        # This reverse needs to be inside the ``setup_method`` method because from
        # the Corporate site we don't define this URL if ``-ext`` module is not
        # installed
        self.url = reverse('doc_search')

    def get_search(self, api_client, search_params):
        return api_client.get(self.url, search_params)

    @pytest.mark.parametrize('page_num', [0, 1])
    def test_search_works_with_title_query(self, api_client, project, page_num):
        query = get_search_query_from_project_file(
            project_slug=project.slug,
            page_num=page_num,
            field='title'
        )

        version = project.versions.all().first()
        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': query
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) >= 1

        # Matching first result
        project_data = data[0]
        assert project_data['project'] == project.slug

        # Check highlight return correct object of first result
        title_highlight = project_data['highlight']['title']

        assert len(title_highlight) == 1
        assert query.lower() in title_highlight[0].lower()

    @pytest.mark.parametrize('data_type', SECTION_FIELDS + DOMAIN_FIELDS)
    @pytest.mark.parametrize('page_num', [0, 1])
    def test_search_works_with_sections_and_domains_query(
        self,
        api_client,
        project,
        page_num,
        data_type
    ):
        type, field = data_type.split('.')
        query = get_search_query_from_project_file(
            project_slug=project.slug,
            page_num=page_num,
            type=type,
            field=field,
        )
        version = project.versions.all().first()
        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': query
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) >= 1

        # Matching first result
        project_data = data[0]
        assert project_data['project'] == project.slug

        inner_hits = project_data['inner_hits']
        # since there was a nested query,
        # inner_hits should not be empty
        assert len(inner_hits) >= 1

        inner_hit_0 = inner_hits[0]  # first inner_hit

        old_type = OLD_TYPES.get(type, type)
        assert inner_hit_0['type'] == old_type

        old_field = old_type + '.' + OLD_FIELDS.get(field, field)
        highlight = inner_hit_0['highlight'][old_field]
        assert (
            len(highlight) == 1
        ), 'number_of_fragments is set to 1'

        # checking highlighting of results
        highlighted_words = re.findall(  # this gets all words inside <em> tag
            '<span>(.*?)</span>',
            highlight[0]
        )
        assert len(highlighted_words) > 0

        for word in highlighted_words:
            # Make it lower because our search is case insensitive
            assert word.lower() in query.lower()

    def test_doc_search_filter_by_project(self, api_client):
        """Test Doc search results are filtered according to project"""

        # `documentation` word is present both in `kuma` and `docs` files
        # and not in `pipeline`, so search with this phrase but filter through project
        search_params = {
            'q': 'documentation',
            'project': 'docs',
            'version': 'latest'
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) == 2  # both pages of `docs` contains the word `documentation`

        # all results must be from same project
        for res in data:
            assert res['project'] == 'docs'

    def test_doc_search_filter_by_version(self, api_client, project):
        """Test Doc search result are filtered according to version"""
        query = get_search_query_from_project_file(project_slug=project.slug)
        latest_version = project.versions.all()[0]
        # Create another version
        dummy_version = G(
            Version,
            project=project,
            active=True,
            privacy_level=PUBLIC,
        )
        # Create HTMLFile same as the latest version
        latest_version_files = HTMLFile.objects.all().filter(version=latest_version)
        for f in latest_version_files:
            f.version = dummy_version
            # Make primary key to None, so django will create new object
            f.pk = None
            f.save()
            PageDocument().update(f)

        search_params = {
            'q': query,
            'project': project.slug,
            'version': dummy_version.slug
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) == 1
        assert data[0]['project'] == project.slug

    def test_doc_search_pagination(self, api_client, project):
        """Test Doc search result can be paginated"""
        latest_version = project.versions.all()[0]
        html_file = HTMLFile.objects.filter(version=latest_version)[0]
        title = html_file.processed_json['title']
        query = title.split()[0]

        # Create 60 more same html file
        for _ in range(60):
            # Make primary key to None, so django will create new object
            html_file.pk = None
            html_file.save()
            PageDocument().update(html_file)

        search_params = {'q': query, 'project': project.slug, 'version': latest_version.slug}
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        # Check the count is 61 (1 existing and 60 new created)
        assert resp.data['count'] == 61
        # Check there are next url
        assert resp.data['next'] is not None
        # There should be only 50 data as the pagination is 50 by default
        assert len(resp.data['results']) == 50

        # Check for page 2
        search_params['page'] = 2
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        # Check the count is 61 (1 existing and 60 new created)
        assert resp.data['count'] == 61
        # We don't have more results after this page
        assert resp.data['next'] is None
        # There should be only the 11 left
        assert len(resp.data['results']) == 11

        # Add `page_size` parameter and check the data is paginated accordingly
        search_params['page_size'] = 5
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        assert len(resp.data['results']) == 5

    def test_doc_search_without_parameters(self, api_client, project):
        """Hitting Document Search endpoint without project and version should return 404."""
        resp = self.get_search(api_client, {})
        assert resp.status_code == 404

    def test_doc_search_without_query(self, api_client, project):
        """Hitting Document Search endpoint without a query should return error."""
        resp = self.get_search(
            api_client, {'project': project.slug, 'version': project.versions.first().slug})
        assert resp.status_code == 400
        # Check error message is there
        assert 'q' in resp.data.keys()

    def test_doc_search_subprojects(self, api_client, all_projects):
        """Test Document search return results from subprojects also"""
        project = all_projects[0]
        subproject = all_projects[1]
        version = project.versions.all()[0]
        # Add another project as subproject of the project
        project.add_subproject(subproject)

        # Now search with subproject content but explicitly filter by the parent project
        query = get_search_query_from_project_file(project_slug=subproject.slug)
        search_params = {
            'q': query,
            'project': project.slug,
            'version': version.slug
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) >= 1  # there may be results from another projects

        # First result should be the subproject
        first_result = data[0]
        assert first_result['project'] == subproject.slug
        # Check the link is the subproject document link
        document_link = subproject.get_docs_url(version_slug=version.slug)
        assert document_link in first_result['link']

    def test_doc_search_unexisting_project(self, api_client):
        project = 'notfound'
        assert not Project.objects.filter(slug=project).exists()

        search_params = {
            'q': 'documentation',
            'project': project,
            'version': 'latest',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 404

    def test_doc_search_unexisting_version(self, api_client, project):
        version = 'notfound'
        assert not project.versions.filter(slug=version).exists()

        search_params = {
            'q': 'documentation',
            'project': project.slug,
            'version': version,
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 404

    @mock.patch.object(PageSearchAPIView, '_get_all_projects', list)
    def test_get_all_projects_returns_empty_results(self, api_client, project):
        """If there is a case where `_get_all_projects` returns empty, we could be querying all projects."""

        # `documentation` word is present both in `kuma` and `docs` files
        # and not in `pipeline`, so search with this phrase but filter through project
        search_params = {
            'q': 'documentation',
            'project': 'docs',
            'version': 'latest'
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) == 0

    def test_doc_search_hidden_versions(self, api_client, all_projects):
        """Test Document search return results from subprojects also"""
        project = all_projects[0]
        subproject = all_projects[1]
        version = project.versions.all()[0]
        # Add another project as subproject of the project
        project.add_subproject(subproject)

        version_subproject = subproject.versions.first()
        version_subproject.hidden = True
        version_subproject.save()

        # Now search with subproject content but explicitly filter by the parent project
        query = get_search_query_from_project_file(project_slug=subproject.slug)
        search_params = {
            'q': query,
            'project': project.slug,
            'version': version.slug
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        # The version from the subproject is hidden, so isn't show on the results.
        data = resp.data['results']
        assert len(data) == 0

        # Now search on the subproject with hidden version
        query = get_search_query_from_project_file(project_slug=subproject.slug)
        search_params = {
            'q': query,
            'project': subproject.slug,
            'version': version_subproject.slug
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200
        # We can still search inside the hidden version
        data = resp.data['results']
        assert len(data) == 1
        first_result = data[0]
        assert first_result['project'] == subproject.slug

    @pytest.mark.parametrize('doctype', [SPHINX, SPHINX_SINGLEHTML, MKDOCS_HTML])
    def test_search_correct_link_for_normal_page_html_projects(self, api_client, doctype):
        project = Project.objects.get(slug='docs')
        project.versions.update(documentation_type=doctype)
        version = project.versions.all().first()

        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': 'Support',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        result = resp.data['results'][0]
        assert result['project'] == project.slug
        assert result['link'].endswith('en/latest/support.html')

    @pytest.mark.parametrize('doctype', [SPHINX, SPHINX_SINGLEHTML, MKDOCS_HTML])
    def test_search_correct_link_for_index_page_html_projects(self, api_client, doctype):
        project = Project.objects.get(slug='docs')
        project.versions.update(documentation_type=doctype)
        version = project.versions.all().first()

        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': 'Some content from index',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        result = resp.data['results'][0]
        assert result['project'] == project.slug
        assert result['link'].endswith('en/latest/index.html')

    @pytest.mark.parametrize('doctype', [SPHINX, SPHINX_SINGLEHTML, MKDOCS_HTML])
    def test_search_correct_link_for_index_page_subdirectory_html_projects(self, api_client, doctype):
        project = Project.objects.get(slug='docs')
        project.versions.update(documentation_type=doctype)
        version = project.versions.all().first()

        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': 'Some content from guides/index',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        result = resp.data['results'][0]
        assert result['project'] == project.slug
        assert result['link'].endswith('en/latest/guides/index.html')

    @pytest.mark.parametrize('doctype', [SPHINX_HTMLDIR, MKDOCS])
    def test_search_correct_link_for_normal_page_htmldir_projects(self, api_client, doctype):
        project = Project.objects.get(slug='docs')
        project.versions.update(documentation_type=doctype)
        version = project.versions.all().first()

        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': 'Support',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        result = resp.data['results'][0]
        assert result['project'] == project.slug
        assert result['link'].endswith('en/latest/support.html')

    @pytest.mark.parametrize('doctype', [SPHINX_HTMLDIR, MKDOCS])
    def test_search_correct_link_for_index_page_htmldir_projects(self, api_client, doctype):
        project = Project.objects.get(slug='docs')
        project.versions.update(documentation_type=doctype)
        version = project.versions.all().first()

        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': 'Some content from index',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        result = resp.data['results'][0]
        assert result['project'] == project.slug
        assert result['link'].endswith('en/latest/')

    @pytest.mark.parametrize('doctype', [SPHINX_HTMLDIR, MKDOCS])
    def test_search_correct_link_for_index_page_subdirectory_htmldir_projects(self, api_client, doctype):
        project = Project.objects.get(slug='docs')
        project.versions.update(documentation_type=doctype)
        version = project.versions.all().first()

        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': 'Some content from guides/index',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        result = resp.data['results'][0]
        assert result['project'] == project.slug
        assert result['link'].endswith('en/latest/guides/')

    def test_search_advanced_query_detection(self, api_client):
        project = Project.objects.get(slug='docs')
        feature, _ = Feature.objects.get_or_create(
            feature_id=Feature.DEFAULT_TO_FUZZY_SEARCH,
        )
        project.feature_set.add(feature)
        project.save()
        version = project.versions.all().first()

        # Query with a typo should return results
        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': 'indx',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        results = resp.data['results']
        assert len(results) > 0
        assert 'Index' in results[0]['title']

        # Query with a typo, but we want to match that
        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': '"indx"',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        assert len(resp.data['results']) == 0

        # Exact query still works
        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': '"index"',
        }
        resp = self.get_search(api_client, search_params)
        assert resp.status_code == 200

        results = resp.data['results']
        assert len(results) > 0
        assert 'Index' in results[0]['title']


class TestDocumentSearch(BaseTestDocumentSearch):

    pass
