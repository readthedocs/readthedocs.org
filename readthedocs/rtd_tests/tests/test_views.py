from django.test import TestCase
from django.contrib.auth.models import User

from projects.models import Project
from projects.forms import UpdateProjectForm


class Testmaker(TestCase):
    fixtures = ["eric"]

    def test_imported_docs(self):
        # Test Import
        self.client.login(username='eric', password='test')
        user = User.objects.get(username='eric')
        r = self.client.get('/dashboard/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/import/manual/', {})
        self.assertEqual(r.status_code, 200)
        form = UpdateProjectForm(data={
            'name': 'Django Kong',
            'repo': 'https://github.com/ericholscher/django-kong',
            'repo_type': 'git',
            'description': 'OOHHH AH AH AH KONG SMASH',
            'language': 'en',
            'default_branch': '',
            'project_url': 'http://django-kong.rtfd.org',
            'default_version': 'latest',
            'privacy_level': 'public',
            'version_privacy_level': 'public',
            'python_interpreter': 'python',
            'documentation_type': 'sphinx',
            'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be',
        }, user=user)
        _ = form.save()
        _ = Project.objects.get(slug='django-kong')

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
