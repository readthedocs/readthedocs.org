import pytest
from django.core.urlresolvers import reverse

from readthedocs.builds.constants import LATEST, STABLE
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search import utils
from readthedocs.search.tests.utils import get_search_query_from_project_file


@pytest.mark.django_db
@pytest.mark.search
class TestSearchUtils:

    @classmethod
    def setup_class(cls):
        # This reverse needs to be inside the ``setup_class`` method because from
        # the Corporate site we don't define this URL if ``-ext`` module is not
        # installed
        cls.url = reverse('doc_search')

    def has_results(self, api_client, project_slug, version_slug):
        query = get_search_query_from_project_file(
            project_slug=project_slug,
        )
        search_params = {
            'project': project_slug,
            'version': version_slug,
            'q': query
        }
        resp = api_client.get(self.url, search_params)
        assert resp.status_code == 200

        data = resp.data['results']
        return len(data) > 0

    def test_remove_only_one_project_index(self, api_client, all_projects):
        project = 'kuma'

        assert self.has_results(api_client, project, LATEST)
        assert self.has_results(api_client, project, STABLE)

        utils.remove_indexed_files(
            HTMLFile,
            project_slug=project,
        )

        assert not self.has_results(api_client, project, LATEST)
        assert not self.has_results(api_client, project, STABLE)

        for project in ['pipeline', 'docs']:
            for version in [LATEST, STABLE]:
                assert self.has_results(api_client, project, version)


    def test_remove_only_one_version_index(self, api_client, all_projects):
        project = 'kuma'

        assert self.has_results(api_client, project, LATEST)
        assert self.has_results(api_client, project, STABLE)

        utils.remove_indexed_files(
            HTMLFile,
            project_slug=project,
            version_slug=LATEST,
        )

        assert not self.has_results(api_client, project, LATEST)
        assert self.has_results(api_client, project, STABLE)

        for project in ['pipeline', 'docs']:
            for version in [LATEST, STABLE]:
                assert self.has_results(api_client, project, version)
