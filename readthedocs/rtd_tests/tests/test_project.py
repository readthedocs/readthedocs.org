from __future__ import absolute_import
import json
from django.test import TestCase
from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Project
from rest_framework.reverse import reverse
from django_dynamic_fixture import get
from readthedocs.restapi.serializers import ProjectSerializer
from readthedocs.rtd_tests.mocks.paths import fake_paths_by_regex


class TestProject(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')

    def test_valid_versions(self):
        r = self.client.get('/api/v2/project/6/valid_versions/', {})
        resp = json.loads(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(resp['flat'][0], '0.8')
        self.assertEqual(resp['flat'][1], '0.8.1')

    def test_subprojects(self):
        r = self.client.get('/api/v2/project/6/subprojects/', {})
        resp = json.loads(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(resp['subprojects'][0]['id'], 23)

    def test_translations(self):
        main_project = get(Project)

        # Create translation of ``main_project``.
        get(Project, main_language_project=main_project)

        url = reverse('project-translations', [main_project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        translation_ids_from_api = [
            t['id'] for t in response.data['translations']]
        translation_ids_from_orm = [
            t[0] for t in main_project.translations.values_list('id')]

        self.assertEqual(
            set(translation_ids_from_api),
            set(translation_ids_from_orm)
        )

    def test_translation_delete(self):
        """Ensure translation deletion doesn't cascade up to main project"""
        # In this scenario, a user has created a project and set the translation
        # to another project. If the user deletes this new project, the delete
        # operation shouldn't cascade up to the main project, and should instead
        # set None on the relation.
        project_keep = get(Project)
        project_delete = get(Project)
        project_delete.translations.add(project_keep)
        self.assertTrue(Project.objects.filter(pk=project_keep.pk).exists())
        self.assertTrue(Project.objects.filter(pk=project_delete.pk).exists())
        self.assertEqual(
            Project.objects.get(pk=project_keep.pk).main_language_project,
            project_delete
        )
        project_delete.delete()
        self.assertFalse(Project.objects.filter(pk=project_delete.pk).exists())
        self.assertTrue(Project.objects.filter(pk=project_keep.pk).exists())
        self.assertIsNone(Project.objects.get(pk=project_keep.pk).main_language_project)

    def test_token(self):
        r = self.client.get('/api/v2/project/6/token/', {})
        resp = json.loads(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(resp['token'], None)

    def test_has_pdf(self):
        # The project has a pdf if the PDF file exists on disk.
        with fake_paths_by_regex('\.pdf$'):
            self.assertTrue(self.pip.has_pdf(LATEST))

        # The project has no pdf if there is no file on disk.
        with fake_paths_by_regex('\.pdf$', exists=False):
            self.assertFalse(self.pip.has_pdf(LATEST))

    def test_has_pdf_with_pdf_build_disabled(self):
        # The project has NO pdf if pdf builds are disabled
        self.pip.enable_pdf_build = False
        with fake_paths_by_regex('\.pdf$'):
            self.assertFalse(self.pip.has_pdf(LATEST))

    def test_has_epub(self):
        # The project has a epub if the PDF file exists on disk.
        with fake_paths_by_regex('\.epub$'):
            self.assertTrue(self.pip.has_epub(LATEST))

        # The project has no epub if there is no file on disk.
        with fake_paths_by_regex('\.epub$', exists=False):
            self.assertFalse(self.pip.has_epub(LATEST))

    def test_has_epub_with_epub_build_disabled(self):
        # The project has NO epub if epub builds are disabled
        self.pip.enable_epub_build = False
        with fake_paths_by_regex('\.epub$'):
            self.assertFalse(self.pip.has_epub(LATEST))
