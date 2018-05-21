import pytest
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from pyquery import PyQuery as pq

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.search import parse_json


@pytest.mark.django_db
@pytest.mark.search
class TestElasticSearch(object):
    url = reverse('search')

    @pytest.fixture(autouse=True)
    def elastic_index(self, mock_parse_json, project, search):
        call_command('reindex_elasticsearch')
        search.refresh_index()

    def test_search_by_project_name(self, client, project):
        resp = client.get(self.url, {'q': project.name})
        assert resp.status_code == 200

        page = pq(resp.content)
        content = page.find('.module-list-wrapper .module-item-title')
        assert project.name.encode('utf-8') in content.text()

    def test_search_by_file_content(self, client, page_json, project):

        versions = project.versions.all()
        # There should be only one version of the project
        assert len(versions) == 1

        data = page_json(version=versions[0])[0]
        # Query with the first word of title
        title = data['title']
        query = title.split()[0]

        resp = client.get(self.url, {'q': query, 'type': 'file'})
        assert resp.status_code == 200

        page = pq(resp.content)
        content = page.find('.module-list-wrapper .module-item-title')
        assert title in content.text()
