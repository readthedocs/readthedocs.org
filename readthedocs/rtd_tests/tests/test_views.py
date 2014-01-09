from django.test import TestCase

from builds.models import Version
from projects.models import Project


class Testmaker(TestCase):
    fixtures = ["eric"]

    def test_imported_docs(self):
        # Test Import
        self.client.login(username='eric', password='test')
        r = self.client.get('/dashboard/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/import/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/dashboard/import/', {
            'repo_type': 'git', 'name': 'Django Kong', 'language': 'en',
            'tags': 'big, fucking, monkey', 'default_branch': '',
            'project_url': 'http://django-kong.rtfd.org',
            'repo': 'https://github.com/ericholscher/django-kong',
            'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be',
            'default_version': 'latest', 'privacy_level': 'public',
            'python_interpreter': 'python', 'version_privacy_level': 'public',
            'description': 'OOHHH AH AH AH KONG SMASH',
            'documentation_type': 'sphinx'})

        kong = Project.objects.get(slug='django-kong')
        Version.objects.create(project=kong, identifier='latest',
                               verbose_name='latest', slug='latest',
                               active=True)
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/docs/django-kong/en/latest/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/django-kong/versions/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/builds/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/django-kong/edit/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/django-kong/subprojects/', {})
        self.assertEqual(r.status_code, 200)
