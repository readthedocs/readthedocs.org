from django.test import TestCase

class Testmaker(TestCase):
    fixtures = ["eric"]

    def setUp(self):
        self.client.login(username='eric', password='test')


    def test_local_built_test(self):
        "A basic smoke test of creating a RTD Built projects"
        r = self.client.get('/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/create/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/dashboard/create/', {'django_packages_url': '', 'name': 'New Proj', 'copyright': 'Eric Holscher', 'tags': '', 'default_branch': '', 'project_url': 'http://example.com', 'theme': 'default', 'version': '1.0', 'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be', 'description': 'Awesome New Project', })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r._headers['location'][1], 'http://testserver/dashboard/new-proj/')
        r = self.client.get('/dashboard/new-proj/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/search/', {'q': 'new proj', })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r._headers['location'][1], 'http://testserver/projects/new-proj/')
        r = self.client.get('/dashboard/new-proj/edit/', {})
        self.assertEqual(r.status_code, 200)

    def test_imported_docs(self):
        r = self.client.get('/dashboard/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/import/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/dashboard/import/', {'repo_type': 'git', 'name': 'Django Kong', 'tags': 'big, fucking, monkey', 'default_branch': '', 'project_url': 'http://django-kong.rtfd.org', 'repo': 'https://github.com/ericholscher/django-kong', 'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be', 'description': 'OOHHH AH AH AH KONG SMASH', })
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/dashboard/django-kong/', {'docs_not_built': 'True', })
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/docs/django-kong/latest/', {})
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/docs/django-kong/en/latest/index.html', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/django-kong/versions/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/dashboard/django-kong/versions/', {'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be', 'version-0.9': 'on', })
        r = self.client.get('/dashboard/django-kong/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/docs/django-kong/0.9/', {})
        self.assertEqual(r.status_code, 302)
        r = self.client.get('/docs/django-kong/en/0.9/index.html', {})
        self.assertEqual(r.status_code, 200)
