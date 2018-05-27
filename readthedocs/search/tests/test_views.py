import pytest
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from pyquery import PyQuery as pq

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from .dummy_data import DUMMY_PAGE_JSON


@pytest.mark.django_db
@pytest.mark.search
class TestElasticSearch(object):
    url = reverse('search')

    @pytest.fixture(autouse=True)
    def elastic_index(self, mock_parse_json, all_projects, search):
        call_command('reindex_elasticsearch')
        search.refresh_index()

    def test_search_by_project_name(self, client, project):
        resp = client.get(self.url, {'q': project.name})
        assert resp.status_code == 200

        page = pq(resp.content)
        content = page.find('.module-list-wrapper .module-item-title')
        assert project.name.encode('utf-8') in content.text().encode('utf-8')

    def test_search_by_file_content(self, client, project):

        versions = project.versions.all()
        # There should be only one version of the project
        assert len(versions) == 1

        data = DUMMY_PAGE_JSON[project.slug][0]
        # Query with the first word of title
        title = data['title']
        query = title.split()[0]

        resp = client.get(self.url, {'q': query, 'type': 'file'})
        assert resp.status_code == 200

        page = pq(resp.content)
        content = page.find('.module-list-wrapper .module-item-title')
        assert title in content.text()

    def test_file_search_show_projects(self, client):
        """Test that search result page shows list of projects while searching for files"""

        # `Installation` word is present both in `kuma` and `pipeline` files
        # so search with this phrase
        resp = client.get(self.url, {'q': "Installation", 'type': 'file'})
        assert resp.status_code == 200

        page = pq(resp.content)
        content = page.find('.module-list-wrapper .module-item-title')

        # There should be 2 search result
        assert len(content) == 2

        # there should be 2 projects in the left side column
        content = page.find('.navigable .project-list')
        assert len(content) == 2
        text = content.text()

        # kuma and pipeline should be there
        assert 'kuma' and 'pipeline' in text

    @pytest.mark.xfail(reason="Versions are not showing correctly! Fixme while rewrite!")
    def test_file_search_show_versions(self, client, all_projects, search, settings):
        # override the settings to index all versions
        settings.INDEX_ONLY_LATEST = False

        project = all_projects[0]
        # Create some versions of the project
        versions = [G(Version, project=project) for _ in range(3)]
        call_command('reindex_elasticsearch')
        search.refresh_index()

        data = DUMMY_PAGE_JSON[project.slug][0]
        title = data['title']
        query = title.split()[0]

        resp = client.get(self.url, {'q': query, 'type': 'file'})
        assert resp.status_code == 200

        page = pq(resp.content)
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
