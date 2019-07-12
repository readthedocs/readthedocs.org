import pytest
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G


from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile
from readthedocs.search.tests.utils import get_search_query_from_project_file
from readthedocs.search.documents import PageDocument


@pytest.mark.django_db
@pytest.mark.search
class TestDocumentSearch:

    @classmethod
    def setup_class(cls):
        # This reverse needs to be inside the ``setup_class`` method because from
        # the Corporate site we don't define this URL if ``-ext`` module is not
        # installed
        cls.url = reverse('doc_search')

    @pytest.mark.parametrize('data_type', ['title'])
    @pytest.mark.parametrize('page_num', [0, 1])
    def test_search_works_with_title_query(self, api_client, project, page_num, data_type):
        query = get_search_query_from_project_file(
            project_slug=project.slug,
            page_num=page_num,
            data_type=data_type
        )

        version = project.versions.all().first()
        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': query
        }
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) >= 1

        # Matching first result
        project_data = data[0]
        assert project_data['project'] == project.slug

        # Check highlight return correct object of first result
        title_highlight = project_data['highlight'][data_type]

        assert len(title_highlight) == 1
        assert query.lower() in title_highlight[0].lower()

    @pytest.mark.parametrize(
        'data_type',
        [
            # page sections fields
            'sections.title',
            'sections.content',

            # domain fields
            'domains.type_display',
            'domains.name',

            # TODO: Add test for "domains.display_name"
        ]
    )
    @pytest.mark.parametrize('page_num', [0, 1])
    def test_search_works_with_sections_and_domains_query(
        self,
        api_client,
        project,
        page_num,
        data_type
    ):
        query = get_search_query_from_project_file(
            project_slug=project.slug,
            page_num=page_num,
            data_type=data_type
        )
        version = project.versions.all().first()
        search_params = {
            'project': project.slug,
            'version': version.slug,
            'q': query
        }
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) >= 1

        # Matching first result
        project_data = data[0]
        assert project_data['project'] == project.slug

        inner_hits = list(project_data['inner_hits'])
        # since there was a nested query,
        # inner_hits should not be empty
        assert len(inner_hits) >= 1

        inner_hit_0 = inner_hits[0]  # first inner_hit

        expected_type = data_type.split('.')[0]  # can be "sections" or "domains"
        assert inner_hit_0['type'] == expected_type

        highlight = inner_hit_0['highlight'][data_type]
        assert (
            len(highlight) == 1
        ), 'number_of_fragments is set to 1'

        # checking highlighting of results
        queries = query.split()  # if query is more than one word
        queries_len = len(queries)
        total_query_words_highlighted = 0

        for q in queries:
            if f'<em>{q.lower()}</em>' in highlight[0].lower():
                total_query_words_highlighted += 1

        if queries_len == 1:
            # if the search was of one word,
            # then the it must be highlighted
            assert total_query_words_highlighted - queries_len <= 0
        else:
            # if the search was of two words or more,
            # then it is not necessary for every word
            # to get highlighted
            assert total_query_words_highlighted - queries_len <= 1

    def test_doc_search_filter_by_project(self, api_client):
        """Test Doc search results are filtered according to project"""

        # `documentation` word is present both in `kuma` and `docs` files
        # and not in `pipeline`, so search with this phrase but filter through project
        search_params = {
            'q': 'documentation',
            'project': 'docs',
            'version': 'latest'
        }
        resp = api_client.get(self.url, search_params)
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
        dummy_version = G(Version, project=project, active=True)
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
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        data = resp.data['results']

        # there may be more than one results
        # for some query like `documentation`
        # for project `kuma`
        assert len(data) >= 1

        # all results must be from same project
        for res in data:
            assert res['project'] == project.slug

    # def test_doc_search_pagination(self, api_client, project):
    #     """Test Doc search result can be paginated"""
    #     latest_version = project.versions.all()[0]
    #     html_file = HTMLFile.objects.filter(version=latest_version)[0]
    #     title = html_file.processed_json['title']
    #     query = title.split()[0]

    #     # Create 60 more same html file
    #     for _ in range(60):
    #         # Make primary key to None, so django will create new object
    #         html_file.pk = None
    #         html_file.save()
    #         PageDocument().update(html_file)

    #     search_params = {'q': query, 'project': project.slug, 'version': latest_version.slug}
    #     resp = api_client.get(self.url, search_params)
    #     assert resp.status_code == 200

    #     # Check the count is 61 (1 existing and 60 new created)
    #     assert resp.data['count'] == 61
    #     # Check there are next url
    #     assert resp.data['next'] is not None
    #     # There should be only 50 data as the pagination is 50 by default
    #     assert len(resp.data['results']) == 50

    #     # Add `page_size` parameter and check the data is paginated accordingly
    #     search_params['page_size'] = 5
    #     resp = api_client.get(self.url, search_params)
    #     assert resp.status_code == 200

    #     assert len(resp.data['results']) == 5

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
        search_params = {
            'q': query,
            'project': project.slug,
            'version': version.slug
        }
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        assert len(data) == 1
        assert data[0]['project'] == subproject.slug
        # Check the link is the subproject document link
        document_link = subproject.get_docs_url(version_slug=version.slug)
        assert document_link in data[0]['link']
