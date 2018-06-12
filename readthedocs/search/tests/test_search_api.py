import pytest
from django.core.urlresolvers import reverse

from readthedocs.search.tests import SearchTestMixin
from .utils import get_search_query_from_project_file


@pytest.mark.django_db
class TestDocSearch(SearchTestMixin):

    @pytest.mark.parametrize('data_type', ['content', 'headers', 'title'])
    @pytest.mark.parametrize('page_num', [0, 1])
    def test_search_works(self, api_client, project, data_type, page_num):
        query = get_search_query_from_project_file(project_slug=project.slug, page_num=page_num,
                                                   data_type=data_type)

        version = project.versions.all()[0]
        url = reverse('doc_search')
        resp = api_client.get(url, {'project': project.slug, 'version': version.slug, 'q': query})
        data = resp.data
        hits = data['results']['hits']

        assert hits['total'] == 1
