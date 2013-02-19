from django.test import TestCase

from builds.models import Version
from projects.models import Project

class RedirectTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        r = self.client.post(
            '/dashboard/import/',
            {'repo_type': 'git', 'name': 'Pip',
             'tags': 'big, fucking, monkey', 'default_branch': '',
             'project_url': 'http://pip.rtfd.org',
             'repo': 'https://github.com/fail/sauce',
             'csrfmiddlewaretoken': '34af7c8a5ba84b84564403a280d9a9be',
             'default_version': 'latest',
             'privacy_level': 'public',
             'version_privacy_level': 'public',
             'description': 'wat',
             'documentation_type': 'sphinx'})
        pip = Project.objects.get(slug='pip')
        pip_latest = Version.objects.create(project=pip, identifier='latest', verbose_name='latest', slug='latest', active=True)


    def test_proper_url_no_slash(self):
        r = self.client.get('/docs/pip')
        # This is triggered by Django, so its a 301, basically just APPEND_SLASH
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r._headers['location'], ('Location', 'http://testserver/docs/pip/'))
        r = self.client.get(r._headers['location'][1])
        self.assertEqual(r.status_code, 302)
        r = self.client.get(r._headers['location'][1])
        self.assertEqual(r.status_code, 200)

    def test_proper_url(self):
        r = self.client.get('/docs/pip/')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r._headers['location'], ('Location', 'http://testserver/docs/pip/en/latest/'))
        r = self.client.get(r._headers['location'][1])
        self.assertEqual(r.status_code, 200)

    def test_inproper_url(self):
        r = self.client.get('/docs/pip/en/')
        self.assertEqual(r.status_code, 404)

    def test_proper_url_full(self):
        r = self.client.get('/docs/pip/en/latest/')
        self.assertEqual(r.status_code, 200)

    # Subdomains

    def test_proper_subdomain(self):
        r = self.client.get('/', HTTP_HOST = 'pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r._headers['location'], ('Location', 'http://pip.readthedocs.org/en/latest/'))

    # Keep this around for now, until we come up with a nicer interface
    """
    def test_inproper_subdomain(self):
        r = self.client.get('/en/', HTTP_HOST = 'pip.readthedocs.org')
        self.assertEqual(r.status_code, 404)
    """ 

    def test_proper_subdomain_and_url(self):
        r = self.client.get('/en/latest/', HTTP_HOST = 'pip.readthedocs.org')
        self.assertEqual(r.status_code, 200)

    # Specific Page Redirects
    def test_proper_page_on_subdomain(self):
        r = self.client.get('/page/test.html', HTTP_HOST = 'pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r._headers['location'], ('Location', 'http://pip.readthedocs.org/en/latest/test.html'))

    # Specific Page Redirects
    def test_proper_page_on_main_site(self):
        r = self.client.get('/docs/pip/page/test.html')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r._headers['location'], ('Location', 'http://testserver/docs/pip/en/latest/test.html'))

    # Test _ -> -
    def test_underscore_redirect(self):
        r = self.client.get('/en/latest/', HTTP_HOST = 'django_kong.readthedocs.org')
        # 404 and not an exception, yay!
        self.assertEqual(r.status_code, 404)
