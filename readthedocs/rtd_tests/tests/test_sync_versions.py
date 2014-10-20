import json

from django.test import TestCase

from builds.models import Version
from projects.models import Project


class TestSyncVersions(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        Version.objects.create(project=self.pip, identifier='origin/master',
                               verbose_name='master', slug='master',
                               active=True)
        Version.objects.create(project=self.pip, identifier='to_delete',
                               verbose_name='to_delete', slug='to_delete',
                               active=False)

    def test_proper_url_no_slash(self):
        version_post_data = {'branches': [
            {
                'identifier': 'origin/master',
                'verbose_name': 'master',
            },
            {
                'identifier': 'origin/to_add',
                'verbose_name': 'to_add',
            },
        ]}

        r = self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk, 
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        json_data = json.loads(r.content)
        self.assertEqual(json_data['deleted_versions'], ['to_delete'])
        self.assertEqual(json_data['added_versions'], ['to_add'])
