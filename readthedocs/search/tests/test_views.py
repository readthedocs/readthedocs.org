import pytest
from django.core.management import call_command
from django.core.urlresolvers import reverse


@pytest.mark.django_db
@pytest.mark.search
class TestElasticSearch(object):

    @pytest.fixture(autouse=True)
    def elastic_index(self, project, search):
        call_command('reindex_elasticsearch')

    def test_search_by_project_name(self, search, client, project):
        url = reverse('search')
        resp = client.get(url, {'q': project.name})
        assert project.name.encode('utf-8') in resp.content
