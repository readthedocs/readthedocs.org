"""Tests for search tasks."""

from unittest import mock
import pytest

from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.projects.models import Project
from readthedocs.search.models import SearchQuery
from readthedocs.search import tasks


@pytest.mark.django_db
@pytest.mark.search
@pytest.mark.usefixtures("all_projects")
class TestSearchTasks:
    @classmethod
    def setup_class(cls):
        # This reverse needs to be inside the ``setup_class`` method because from
        # the Corporate site we don't define this URL if ``-ext`` module is not
        # installed
        cls.url = reverse("search_api")

    def test_search_query_recorded_when_results_not_zero(self, api_client):
        """Test if search query is recorded in a database when a search is made."""

        assert (
            SearchQuery.objects.all().count() == 0
        ), "no SearchQuery should be present if there is no search made."

        # `sphinx` is present in `documentation.json`
        # file of project `kuma`
        search_params = {"q": "sphinx", "project": "kuma", "version": "latest"}
        resp = api_client.get(self.url, search_params)

        assert resp.data["count"] == 1
        assert (
            SearchQuery.objects.all().count() == 1
        ), "there should be 1 obj since a search is made which returns one result."

    def test_partial_queries_are_not_recorded(self, api_client):
        """Test if partial queries are not recorded."""

        assert (
            SearchQuery.objects.all().count() == 0
        ), "no SearchQuery should be present if there is no search made."

        time = timezone.now()
        search_params = {"q": "stack", "project": "docs", "version": "latest"}

        with mock.patch("django.utils.timezone.now") as test_time:
            test_time.return_value = time
            resp = api_client.get(self.url, search_params)
            assert resp.status_code, 200

        assert (
            SearchQuery.objects.all().count() == 1
        ), "one SearchQuery should be present"

        # update the time and the search query and make another search request
        time = time + timezone.timedelta(seconds=2)
        search_params["q"] = "stack over"
        with mock.patch("django.utils.timezone.now") as test_time:
            test_time.return_value = time
            resp = api_client.get(self.url, search_params)
            assert resp.status_code, 200

        # update the time and the search query and make another search request
        time = time + timezone.timedelta(seconds=2)
        search_params["q"] = "stack overflow"
        with mock.patch("django.utils.timezone.now") as test_time:
            test_time.return_value = time
            resp = api_client.get(self.url, search_params)
            assert resp.status_code, 200

        assert (
            SearchQuery.objects.all().count() == 1
        ), "one SearchQuery should be present"
        assert (
            SearchQuery.objects.all().first().query == "stack overflow"
        ), "one SearchQuery should be there because partial queries gets updated"

    def test_search_query_recorded_when_results_are_zero(self, api_client):
        """Test that search queries are recorded when they have zero results."""

        assert (
            SearchQuery.objects.all().count() == 0
        ), "no SearchQuery should be present if there is no search made."

        # `readthedo` is NOT present in project `kuma`.
        search_params = {"q": "readthedo", "project": "kuma", "version": "latest"}
        resp = api_client.get(self.url, search_params)

        assert resp.data["count"] == 0
        assert SearchQuery.objects.all().count() == 1

    def test_delete_old_search_queries_from_db(self, project):
        """Test that the old search queries are being deleted."""

        assert (
            SearchQuery.objects.all().count() == 0
        ), "no SearchQuery should be present if there is no search made."

        obj = SearchQuery.objects.create(
            project=project, version=project.versions.all().first(), query="first"
        )
        obj.created = timezone.make_aware(timezone.datetime(2019, 1, 1))
        obj.save()

        assert SearchQuery.objects.all().count() == 1
        tasks.delete_old_search_queries_from_db()
        assert SearchQuery.objects.all().count() == 0


@pytest.mark.django_db
class TestRecordSearchQueryBatch:
    def setup_method(self):
        self.project_a = get(Project, slug="project-a", versions=[])
        self.version_a = self.project_a.versions.get(slug="latest")
        self.project_b = get(Project, slug="project-b", versions=[])
        self.version_b = self.project_b.versions.get(slug="latest")

    def test_missing_version_does_not_skip_other_projects(self):
        tasks.record_search_query_batch(
            projects_and_versions=[
                ("project-a", "does-not-exist"),
                ("project-b", "latest"),
            ],
            query="sphinx",
            total_results=3,
            time_string=timezone.now().isoformat(),
        )

        assert list(SearchQuery.objects.values_list("project__slug", "version__slug", "query")) == [
            ("project-b", "latest", "sphinx"),
        ]

    def test_records_all_projects_in_batch(self):
        tasks.record_search_query_batch(
            projects_and_versions=[("project-a", "latest"), ("project-b", "latest")],
            query="sphinx",
            total_results=3,
            time_string=timezone.now().isoformat(),
        )

        assert set(SearchQuery.objects.values_list("version_id", "query", "total_results")) == {
            (self.version_a.pk, "sphinx", 3),
            (self.version_b.pk, "sphinx", 3),
        }

    def test_partial_query_is_updated(self):
        partial = get(
            SearchQuery,
            project=self.project_a,
            version=self.version_a,
            query="sph",
            total_results=10,
        )
        old_modified = partial.modified

        tasks.record_search_query_batch(
            projects_and_versions=[("project-a", "latest")],
            query="sphinx",
            total_results=3,
            time_string=timezone.now().isoformat(),
        )

        assert SearchQuery.objects.count() == 1
        partial.refresh_from_db()
        assert partial.query == "sphinx"
        assert partial.total_results == 3
        assert partial.modified > old_modified
