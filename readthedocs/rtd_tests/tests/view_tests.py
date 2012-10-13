from django.test import TestCase

class Testmaker(TestCase):
    fixtures = ["eric"]

    def setUp(self):
        self.client.login(username='eric', password='test')

    def test_imported_docs(self):
        r = self.client.get('/dashboard/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/import/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.post(
            '/dashboard/import/',
            {'repo_type': 'git', 'name': 'Django Kong',
             'tags': 'big, fucking, monkey', 'default_branch': '',
             'project_url': 'http://django-kong.rtfd.org',
             'repo': 'https://github.com/ericholscher/django-kong',
             'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be',
             'default_version': 'latest',
             'description': 'OOHHH AH AH AH KONG SMASH',
             'documentation_type': 'sphinx'})
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/docs/django-kong/latest/', {})
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/docs/django-kong/en/latest/index.html', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/django-kong/versions/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/dashboard/django-kong/versions/', {'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be', 'version-0.9': 'on', })
        r = self.client.get('/docs/django-kong/0.9/', {})
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/docs/django-kong/en/0.9/index.html', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/builds/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/builds/django-kong/1/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/django-kong/edit/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/django-kong/subprojects/', {})
        self.assertEqual(r.status_code, 200)
