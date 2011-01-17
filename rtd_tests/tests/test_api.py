from django.test import TestCase
import json
import base64

class BasicTests(TestCase):
    fixtures = ['eric.json']

    def test_make_project(self):
        """
        Test that a superuser can use the API
        """
        post_data = {"user": "/api/v1/user/1/",
                     "name": "awesome-project",
                     "repo": "https://github.com/ericholscher/django-kong.git"
                     }
        resp = self.client.post('/api/v1/project/',
                                data=json.dumps(post_data),
                                content_type='application/json',
                                HTTP_AUTHORIZATION='Basic %s' % base64.b64encode('eric:test')
                                )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp['location'],
                         'http://testserver/api/v1/project/1/')
        resp = self.client.get('/api/v1/project/1/',
                               data={'format': 'json'},
                                HTTP_AUTHORIZATION='Basic %s' % base64.b64encode('eric:test')
                              )
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['slug'], 'awesome-project')


    def test_invalid_make_project(self):
        """
        Test that the non-superuser can't make a user
        """
        post_data = {"user": "/api/v1/user/2/",
                     "name": "awesome-project-2",
                     "repo": "https://github.com/ericholscher/django-bob.git"
                     }
        resp = self.client.post('/api/v1/project/',
                                data=json.dumps(post_data),
                                content_type='application/json',
                                HTTP_AUTHORIZATION='Basic %s' % base64.b64encode('test:test')
                                )
        self.assertEqual(resp.status_code, 401)
