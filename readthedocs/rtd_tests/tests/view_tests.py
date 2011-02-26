from django.test import TestCase

class Testmaker(TestCase):
    fixtures = ["eric"]

    def test_local_built_test(self):
        "A basic smoke test of creating a RTD Built projects"
        self.assertTrue(self.client.login(username='eric', password='test'))
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
