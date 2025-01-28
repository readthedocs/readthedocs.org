import pytest
from django.core.management import call_command
from django.test import TestCase, override_settings
from django_dynamic_fixture import get
from elasticsearch.exceptions import NotFoundError

from readthedocs.projects.models import Project
from readthedocs.search.documents import ProjectDocument


@pytest.mark.search
@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class TestSignals(TestCase):
    def setUp(self):
        call_command("search_index", "--delete", "-f")
        call_command("search_index", "--create")

    def tearDown(self):
        super().tearDown()
        call_command("search_index", "--delete", "-f")

    def test_project_index_is_updated(self):
        project = get(
            Project,
            slug="testing",
            name="A testing project",
            description="Just another project",
        )
        id = project.id

        # Check initial values
        result = ProjectDocument.get(id=id)
        self.assertEqual(project.slug, result.slug)
        self.assertEqual(project.name, result.name)
        self.assertEqual(project.language, result.language)
        self.assertEqual(project.description, result.description)

        project.name = "A new name"
        project.description = "Just another cool project"
        project.save()

        # Check after update
        result = ProjectDocument.get(id=id)
        self.assertEqual(project.slug, result.slug)
        self.assertEqual(project.name, result.name)
        self.assertEqual(project.language, result.language)
        self.assertEqual(project.description, result.description)

        project.delete()
        # Check after deletion
        with pytest.raises(NotFoundError):
            ProjectDocument.get(id=id)
