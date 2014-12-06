import json

from django.test import TestCase

from projects.models import Project
from .projects_factories import ProjectFactory


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
        r = self.client.get('/api/v2/project/6/translations/', {})
        self.assertEqual(r.status_code, 200)

    def test_token(self):
        r = self.client.get('/api/v2/project/6/token/', {})
        resp = json.loads(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(resp['token'], None)

class ProjectCommentTests(TestCase):
    
    def test_commentable_project_uses_builder_with_commentable_versioning_method(self):
        '''
        Even though we show the user a boolean "commentable" option,
        we compose this knowledge as a separate class, WebSupportBuilder.
        '''
        project = ProjectFactory(allow_comments=True)
        builder = project.doc_builder()
        self.assertEqual(getattr(builder, 'versioning_method', None), "commentable")
        
    def test_uncommentable_project_uses_builder_without_commentable_verioning_method(self):
        project = ProjectFactory(allow_comments=False)
        builder = project.doc_builder()
        self.assertNotEqual(getattr(builder, 'versioning_method', None), "commentable")
