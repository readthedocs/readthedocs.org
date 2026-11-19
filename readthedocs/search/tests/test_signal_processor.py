from unittest import mock

import pytest
from django.db import connection
from django.db.models.signals import post_delete, pre_delete
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django_dynamic_fixture import get
from django_elasticsearch_dsl.registries import registry

from readthedocs.builds.models import Build, BuildCommandResult
from readthedocs.projects.models import HTMLFile, ImportedFile, Project


def test_documents_dont_rely_on_django_elasticsearch_dsl_signals():
    # We don't use the real-time signal processor from django-elasticsearch-dsl,
    # documents must be indexed from our own receivers and tasks.
    for document in registry.get_documents():
        assert document.django.ignore_signals is True
        assert document.django.related_models == []


@pytest.mark.parametrize("model", [ImportedFile, HTMLFile, Build, BuildCommandResult])
def test_no_delete_receivers_on_non_indexed_models(model):
    # Delete receivers disable Django's fast delete (no SELECT before the DELETE).
    assert not pre_delete.has_listeners(model)
    assert not post_delete.has_listeners(model)


class TestDeleteQueries(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = self.project.versions.get(slug="latest")

    def test_imported_files_queryset_delete_is_a_single_query(self):
        for i in range(3):
            get(HTMLFile, project=self.project, version=self.version, build=1, name=f"{i}.html")

        with self.assertNumQueries(1):
            ImportedFile.objects.filter(version=self.version).exclude(build=2).delete()

        assert not ImportedFile.objects.filter(version=self.version).exists()

    def test_build_commands_are_deleted_without_selecting_them(self):
        build = get(Build, project=self.project, version=self.version)
        for i in range(3):
            get(BuildCommandResult, build=build, command=f"cmd {i}")

        with CaptureQueriesContext(connection) as context:
            Build.objects.filter(pk=build.pk).delete()

        queries = [query["sql"] for query in context.captured_queries]
        assert not any("SELECT" in sql and "builds_buildcommandresult" in sql for sql in queries)
        assert (
            f'DELETE FROM "builds_buildcommandresult" WHERE "builds_buildcommandresult"."build_id" IN ({build.pk})'
            in queries
        )

        assert not BuildCommandResult.objects.filter(build_id=build.pk).exists()


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class TestProjectIndexing(TestCase):
    @mock.patch("readthedocs.search.signals.index_objects_to_es")
    def test_project_is_indexed_on_save(self, index_objects_to_es):
        project = get(Project)
        index_objects_to_es.delay.assert_called_with(
            app_label="projects",
            model_name="Project",
            document_class="<class 'readthedocs.search.documents.ProjectDocument'>",
            objects_id=[project.id],
        )

    @mock.patch("readthedocs.search.signals.delete_objects_in_es")
    def test_project_is_removed_on_delete(self, delete_objects_in_es):
        project = get(Project)
        project_id = project.id
        project.delete()
        delete_objects_in_es.assert_called_once_with(
            app_label="projects",
            model_name="Project",
            document_class="<class 'readthedocs.search.documents.ProjectDocument'>",
            objects_id=[project_id],
        )
