from bamboo_boy.utils import with_canopy
import json
from django.test import TestCase
from projects.models import Project
from rtd_tests.factories.projects_factories import OneProjectWithTranslationsOneWithout,\
    ProjectFactory
from rest_framework.reverse import reverse
from restapi.serializers import ProjectSerializer


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
