from bamboo_boy.utils import with_canopy
import json
from django.test import TestCase
from builds.constants import LATEST
from projects.models import Project
from rtd_tests.factories.projects_factories import OneProjectWithTranslationsOneWithout,\
    ProjectFactory
from rest_framework.reverse import reverse
from restapi.serializers import ProjectSerializer
from rtd_tests.mocks.paths import fake_paths_by_regex


@with_canopy(OneProjectWithTranslationsOneWithout)
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
        p = self.canopy.project_with_translations
        url = reverse('project-translations', [p.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        translation_ids_from_api = [t['id']
                                    for t in response.data['translations']]
        translation_ids_from_orm = [t[0]
                                    for t in p.translations.values_list('id')]

        self.assertEqual(
            set(translation_ids_from_api),
            set(translation_ids_from_orm)
        )

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
