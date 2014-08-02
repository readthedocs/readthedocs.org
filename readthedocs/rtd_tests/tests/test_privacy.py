import logging
import json

from django.test import TestCase

from builds.models import Version
from projects.models import Project
from projects import tasks

log = logging.getLogger(__name__)


class PrivacyTests(TestCase):
    fixtures = ["eric"]

    def tearDown(self):
        tasks.update_docs = self.old_bd

    def setUp(self):
        self.old_bd = tasks.update_docs

        def mock(*args, **kwargs):
            pass
            #log.info("Mocking for great profit and speed.")
        tasks.update_docs.delay = mock

    def _create_kong(self, privacy_level='private',
                     version_privacy_level='private'):
        self.client.login(username='eric', password='test')
        log.info(("Making kong with privacy: %s and version privacy: %s"
                  % (privacy_level, version_privacy_level)))
        r = self.client.post(
            '/dashboard/import/',
            {'repo_type': 'git', 'name': 'Django Kong', 'language': 'en',
             'tags': 'big, fucking, monkey', 'default_branch': '',
             'project_url': 'http://django-kong.rtfd.org',
             'repo': 'https://github.com/ericholscher/django-kong',
             'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be',
             'default_version': 'latest',
             'python_interpreter': 'python',
             'privacy_level': privacy_level,
             'version_privacy_level': version_privacy_level,
             'description': 'OOHHH AH AH AH KONG SMASH',
             'documentation_type': 'sphinx'})
        self.assertEqual(r.status_code, 302)
        r = self.client.post(
            '/dashboard/django-kong/advanced/',
            {'tags': 'big, fucking, monkey', 'default_branch': '',
             'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be',
             'default_version': 'latest',
             'python_interpreter': 'python',
             'privacy_level': privacy_level,
             'num_minor': 2, 'num_major': 2, 'num_point': 2,
             'version_privacy_level': version_privacy_level,
             'documentation_type': 'sphinx'})

        self.assertAlmostEqual(Project.objects.count(), 1)
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        return Project.objects.get(slug='django-kong')

    def test_private_repo(self):
        """Check that private projects don't show up in: builds, downloads,
        detail, homepage

        """
        self._create_kong('private', 'private')

        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/builds/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)

        self.client.login(username='tester', password='test')
        r = self.client.get('/')
        self.assertTrue('Django Kong' not in r.content)
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 404)
        r = self.client.get('/builds/django-kong/')
        self.assertEqual(r.status_code, 404)
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 404)

    def test_protected_repo(self):
        """Check that protected projects don't show up in: builds, downloads,
        detail, project list

        """
        self._create_kong('protected', 'protected')

        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/')
        self.assertTrue('Django Kong' in r.content)
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/builds/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)

        self.client.login(username='tester', password='test')
        r = self.client.get('/')
        self.assertTrue('Django Kong' not in r.content)
        r = self.client.get('/projects/')
        self.assertTrue('Django Kong' not in r.content)
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/builds/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)

    def test_public_repo(self):
        """Check that public projects show up in: builds, downloads, detail,
        homepage

        """
        self._create_kong('public', 'public')

        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/builds/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)

        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/builds/django-kong/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)

    def test_private_branch(self):
        kong = self._create_kong('public', 'private')

        self.client.login(username='eric', password='test')
        Version.objects.create(project=kong, identifier='test id',
                               verbose_name='test verbose', slug='test-slug')
        r = self.client.post('/dashboard/django-kong/versions/',
                             {'version-test-slug': 'on',
                              'privacy-test-slug': 'private'})
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Version.objects.all()[0].privacy_level, 'private')
        r = self.client.get('/projects/django-kong/')
        self.assertTrue('test-slug' in r.content)

        # Make sure it doesn't show up as tester
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertTrue('test-slug' not in r.content)

    def test_protected_branch(self):
        kong = self._create_kong('public', 'protected')

        self.client.login(username='eric', password='test')
        Version.objects.create(project=kong, identifier='test id',
                               verbose_name='test verbose', slug='test-slug')
        r = self.client.post('/dashboard/django-kong/versions/',
                             {'version-test-slug': 'on',
                              'privacy-test-slug': 'protected'})
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Version.objects.all()[0].privacy_level, 'protected')
        r = self.client.get('/projects/django-kong/')
        self.assertTrue('test-slug' in r.content)

        # Make sure it doesn't show up as tester
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertTrue('test-slug' not in r.content)

    def test_public_branch(self):
        kong = self._create_kong('public', 'public')

        self.client.login(username='eric', password='test')
        Version.objects.create(project=kong, identifier='test id',
                               verbose_name='test verbose', slug='test-slug')
        r = self.client.post('/dashboard/django-kong/versions/',
                             {'version-test-slug': 'on',
                              'privacy-test-slug': 'public'})
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Version.objects.all()[0].privacy_level, 'public')
        r = self.client.get('/projects/django-kong/')
        self.assertTrue('test-slug' in r.content)

        # Make sure it doesn't show up as tester
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertTrue('test-slug' in r.content)

    def test_public_repo_api(self):
        self._create_kong('public', 'public')
        self.client.login(username='eric', password='test')
        resp = self.client.get("http://testserver/api/v1/project/django-kong/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get("http://testserver/api/v1/project/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 1)

        self.client.login(username='tester', password='test')
        resp = self.client.get("http://testserver/api/v1/project/django-kong/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get("http://testserver/api/v1/project/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 1)

    def test_protected_repo_api(self):
        self._create_kong('protected', 'protected')
        self.client.login(username='eric', password='test')
        resp = self.client.get("http://testserver/api/v1/project/django-kong/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get("http://testserver/api/v1/project/",
                               data={"format": "json"})
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 1)

        self.client.login(username='tester', password='test')
        resp = self.client.get("http://testserver/api/v1/project/",
                               data={"format": "json"})
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 0)

        # Need to figure out how to properly filter the detail view in
        # tastypie.  Protected stuff won't show up in detail pages on the API
        # currently.
        """
        resp = self.client.get("http://testserver/api/v1/project/django-kong/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        """

    def test_private_repo_api(self):
        self._create_kong('private', 'private')
        self.client.login(username='eric', password='test')
        resp = self.client.get("http://testserver/api/v1/project/django-kong/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get("http://testserver/api/v1/project/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 1)

        self.client.login(username='tester', password='test')
        resp = self.client.get("http://testserver/api/v1/project/django-kong/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get("http://testserver/api/v1/project/",
                               data={"format": "json"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['meta']['total_count'], 0)

    def test_private_doc_serving(self):
        kong = self._create_kong('public', 'private')

        self.client.login(username='eric', password='test')
        Version.objects.create(project=kong, identifier='test id',
                               verbose_name='test verbose', slug='test-slug')
        self.client.post('/dashboard/django-kong/versions/',
                         {'version-test-slug': 'on',
                          'privacy-test-slug': 'private'})
        r = self.client.get('/docs/django-kong/en/test-slug/')
        self.client.login(username='eric', password='test')
        self.assertEqual(r.status_code, 200)

        # Make sure it doesn't show up as tester
        self.client.login(username='tester', password='test')
        r = self.client.get('/docs/django-kong/en/test-slug/')
        self.assertEqual(r.status_code, 401)
