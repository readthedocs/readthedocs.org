import time

import pytest
from django.urls import reverse

from readthedocs.builds.constants import LATEST, STABLE
from readthedocs.projects.models import HTMLFile
from readthedocs.search import utils
from readthedocs.search.tests.utils import get_search_query_from_project_file


@pytest.mark.django_db
@pytest.mark.search
@pytest.mark.proxito
class TestSearchUtils:

    def setup_method(self):
        self.url = reverse('search_api')

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
        # Deletion of indices from ES happens async,
        # so we need to wait a little before checking for results.
        time.sleep(1)

        assert self.has_results(api_client, project, LATEST) is False
        assert self.has_results(api_client, project, STABLE) is False
        # Check that other projects weren't deleted
        for project in ['pipeline', 'docs']:
            for version in [LATEST, STABLE]:
                assert self.has_results(api_client, project, version) is True

    def test_remove_only_one_version_index(self, api_client, all_projects):
        project = 'kuma'

        assert self.has_results(api_client, project, LATEST)
        assert self.has_results(api_client, project, STABLE)

        utils.remove_indexed_files(
            HTMLFile,
            project_slug=project,
            version_slug=LATEST,
        )

        # Deletion of indices from ES happens async,
        # so we need to wait a little before checking for results.
        time.sleep(1)

        assert self.has_results(api_client, project, LATEST) is False
        # Only latest was deleted.
        assert self.has_results(api_client, project, STABLE) is True

        for project in ['pipeline', 'docs']:
            for version in [LATEST, STABLE]:
                assert self.has_results(api_client, project, version)
