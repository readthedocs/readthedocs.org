import json

from django.test import TestCase

from projects.models import Project


class Testmaker(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.latest = self.pip.versions.create_latest()

    def test_footer(self):
        r = self.client.get('/api/v2/footer_html/?project=pip&version=latest&page=index', {})
        resp = json.loads(r.content)
        self.assertEqual(resp['version_active'], True)
        self.assertEqual(resp['version_supported'], True)
        self.assertEqual(r.context['main_project'], self.pip)
        self.assertEqual(r.status_code, 200)

        self.latest.active = False
        self.latest.save()
        r = self.client.get('/api/v2/footer_html/?project=pip&version=latest&page=index', {})
        resp = json.loads(r.content)
        self.assertEqual(resp['version_active'], False)
        self.assertEqual(r.status_code, 200)

