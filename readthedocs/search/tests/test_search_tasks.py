"""Tests for search tasks."""

import pytest

from django.urls import reverse
from django.utils import timezone

from readthedocs.projects.models import Project
from readthedocs.builds.models import Version
from readthedocs.search.models import SearchQuery
from readthedocs.search import tasks


@pytest.mark.django_db
@pytest.mark.search
class TestSearchTasks:

    @classmethod
    def setup_class(cls):
        # This reverse needs to be inside the ``setup_class`` method because from
        # the Corporate site we don't define this URL if ``-ext`` module is not
        # installed
        cls.url = reverse('doc_search')

    def test_search_query_recorded_when_results_not_zero(self, api_client):
        """Test if search query is recorded in a database when a search is made."""

        assert (
            SearchQuery.objects.all().count() == 0
        ), 'no SearchQuery should be present if there is no search made.'

        # `sphinx` is present in `documentation.json`
        # file of project `kuma`
        search_params = {
            'q': 'sphinx',
            'project': 'kuma',
            'version': 'latest'
        }
        resp = api_client.get(self.url, search_params)

        assert (resp.data['count'] == 1)
        assert (
            SearchQuery.objects.all().count() == 1
        ), 'there should be 1 obj since a search is made which returns one result.'

    def test_search_query_not_recorded_when_results_are_zero(self, api_client):
        """Test that search queries are not recorded when they have zero results."""

        assert (
            SearchQuery.objects.all().count() == 0
        ), 'no SearchQuery should be present if there is no search made.'

        # `readthedo` is NOT present in project `kuma`.
        search_params = {
            'q': 'readthedo',
            'project': 'kuma',
            'version': 'latest'
        }
        resp = api_client.get(self.url, search_params)

        assert (resp.data['count'] == 0)
        assert (
            SearchQuery.objects.all().count() == 0
        ), 'there should be 0 obj since there were no results.'

    def test_delete_old_search_queries_from_db(self, project):
        """Test that the old search queries are being deleted."""

        assert (
            SearchQuery.objects.all().count() == 0
        ), 'no SearchQuery should be present if there is no search made.'

        obj = SearchQuery.objects.create(
            project=project,
            version=project.versions.all().first(),
            query='first'
        )
        obj.created = timezone.make_aware(timezone.datetime(2019, 1, 1))
        obj.save()

        assert SearchQuery.objects.all().count() == 1
        tasks.delete_old_search_queries_from_db()
        assert SearchQuery.objects.all().count() == 0
