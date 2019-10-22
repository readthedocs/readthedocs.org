"""Tests for search tasks."""

import mock
import pytest

from django.urls import reverse
from django.utils import timezone

from readthedocs.projects.models import Project
from readthedocs.builds.models import Version
from readthedocs.search.models import SearchQuery, PageView
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

    def test_partial_queries_are_not_recorded(self, api_client):
        """Test if partial queries are not recorded."""

        assert (
            SearchQuery.objects.all().count() == 0
        ), 'no SearchQuery should be present if there is no search made.'

        time = timezone.now()
        search_params = { 'q': 'stack', 'project': 'docs', 'version': 'latest' }

        with mock.patch('django.utils.timezone.now') as test_time:
            test_time.return_value = time
            resp = api_client.get(self.url, search_params)
            assert resp.status_code, 200

        assert (
            SearchQuery.objects.all().count() == 1
        ), 'one SearchQuery should be present'

        # update the time and the search query and make another search request
        time = time + timezone.timedelta(seconds=2)
        search_params['q'] = 'stack over'
        with mock.patch('django.utils.timezone.now') as test_time:
            test_time.return_value = time
            resp = api_client.get(self.url, search_params)
            assert resp.status_code, 200

        # update the time and the search query and make another search request
        time = time + timezone.timedelta(seconds=2)
        search_params['q'] = 'stack overflow'
        with mock.patch('django.utils.timezone.now') as test_time:
            test_time.return_value = time
            resp = api_client.get(self.url, search_params)
            assert resp.status_code, 200

        assert (
            SearchQuery.objects.all().count() == 1
        ), 'one SearchQuery should be present'
        assert (
            SearchQuery.objects.all().first().query == 'stack overflow'
        ), 'one SearchQuery should be there because partial queries gets updated'

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

    def test_increase_page_view_count(self, project):
        today = timezone.now()
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        yesterday = timezone.now() - timezone.timedelta(days=1)

        assert (
            PageView.objects.all().count() == 0
        ), 'There\'s no PageView object created yet.'

        # testing for yesterday
        with mock.patch('readthedocs.search.tasks.timezone.now') as mocked_timezone:
            mocked_timezone.return_value = yesterday

            tasks.increase_page_view_count(
                project_slug=project.slug,
                version_slug=project.versions.all().first().slug,
                path='index',
            )

            assert (
                PageView.objects.all().count() == 1
            ), 'PageView object for path \'index\' is created'
            assert (
                PageView.objects.all().first().view_count == 1
            ), '\'index\' has 1 view'

            tasks.increase_page_view_count(
                project_slug=project.slug,
                version_slug=project.versions.all().first().slug,
                path='index',
            )

            assert (
                PageView.objects.all().count() == 1
            ), 'PageView object for path \'index\' is already created'
            assert (
                PageView.objects.all().first().view_count == 2
            ), '\'index\' has 2 views now'

        # testing for today
        with mock.patch('readthedocs.search.tasks.timezone.now') as mocked_timezone:
            mocked_timezone.return_value = today
            tasks.increase_page_view_count(
                project_slug=project.slug,
                version_slug=project.versions.all().first().slug,
                path='index',
            )

            assert (
                PageView.objects.all().count() == 2
            ), 'PageView object for path \'index\' is created for two days (yesterday and today)'
            assert (
                PageView.objects.all().order_by('-date').first().view_count == 1
            ), '\'index\' has 1 view today'

        # testing for tomorrow
        with mock.patch('readthedocs.search.tasks.timezone.now') as mocked_timezone:
            mocked_timezone.return_value = tomorrow
            tasks.increase_page_view_count(
                project_slug=project.slug,
                version_slug=project.versions.all().first().slug,
                path='index',
            )

            assert (
                PageView.objects.all().count() == 3
            ), 'PageView object for path \'index\' is created for three days (yesterday, today & tomorrow)'
            assert (
                PageView.objects.all().order_by('-date').first().view_count == 1
            ), '\'index\' has 1 view tomorrow'
