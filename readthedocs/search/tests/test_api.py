import pytest
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G


from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile
from readthedocs.search.tests.utils import get_search_query_from_project_file


@pytest.mark.django_db
@pytest.mark.search
class TestDocumentSearch(object):

    @classmethod
    def setup_class(cls):
        # This reverse needs to be inside the ``setup_class`` method because from
        # the Corporate site we don't define this URL if ``-ext`` module is not
        # installed
        cls.url = reverse('doc_search')

    @pytest.mark.parametrize('data_type', ['content', 'headers', 'title'])
    @pytest.mark.parametrize('page_num', [0, 1])
    def test_search_works(self, api_client, project, data_type, page_num):
        query = get_search_query_from_project_file(project_slug=project.slug, page_num=page_num,
                                                   data_type=data_type)

        version = project.versions.all()[0]
        search_params = {'project': project.slug, 'version': version.slug, 'q': query}
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) == 1
        project_data = data[0]
        assert project_data['project'] == project.slug

        # Check highlight return correct object
        all_highlights = project_data['highlight'][data_type]
        for highlight in all_highlights:
            # Make it lower because our search is case insensitive
            assert query.lower() in highlight.lower()

    def test_doc_search_filter_by_project(self, api_client):
        """Test Doc search result are filtered according to project"""

        # `Github` word is present both in `kuma` and `pipeline` files
        # so search with this phrase but filter through `kuma` project
        search_params = {'q': 'GitHub', 'project': 'kuma', 'version': 'latest'}
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) == 1
        assert data[0]['project'] == 'kuma'

    def test_doc_search_filter_by_version(self, api_client, project):
        """Test Doc search result are filtered according to version"""
        query = get_search_query_from_project_file(project_slug=project.slug)
        latest_version = project.versions.all()[0]
        # Create another version
        dummy_version = G(Version, project=project)
        # Create HTMLFile same as the latest version
        latest_version_files = HTMLFile.objects.all().filter(version=latest_version)
        for f in latest_version_files:
            f.version = dummy_version
            # Make primary key to None, so django will create new object
            f.pk = None
            f.save()

        search_params = {'q': query, 'project': project.slug, 'version': dummy_version.slug}
        resp = api_client.get(self.url, search_params)
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

        # Create 30 more same html file
        for _ in range(30):
            # Make primary key to None, so django will create new object
            html_file.pk = None
            html_file.save()

        search_params = {'q': query, 'project': project.slug, 'version': latest_version.slug}
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        # Check the count is 31 (1 existing and 30 new created)
        assert resp.data['count'] == 31
        # Check there are next url
        assert resp.data['next'] is not None
        # There should be only 25 data as the pagination is 25 by default
        assert len(resp.data['results']) == 25

        # Add `page_size` parameter and check the data is paginated accordingly
        search_params['page_size'] = 5
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        assert len(resp.data['results']) == 5

    def test_doc_search_without_parameters(self, api_client, project):
        """Hitting Document Search endpoint without query parameters should return error"""
        resp = api_client.get(self.url)
        assert resp.status_code == 400
        # Check error message is there
        assert sorted(['q', 'project', 'version']) == sorted(resp.data.keys())

    def test_doc_search_subprojects(self, api_client, all_projects):
        """Test Document search return results from subprojects also"""
        project = all_projects[0]
        subproject = all_projects[1]
        version = project.versions.all()[0]
        # Add another project as subproject of the project
        project.add_subproject(subproject)

        # Now search with subproject content but explicitly filter by the parent project
        query = get_search_query_from_project_file(project_slug=subproject.slug)
        search_params = {'q': query, 'project': project.slug, 'version': version.slug}
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) == 1
        assert data[0]['project'] == subproject.slug
        # Check the link is the subproject document link
        document_link = subproject.get_docs_url(version_slug=version.slug)
        assert document_link in data[0]['link']
