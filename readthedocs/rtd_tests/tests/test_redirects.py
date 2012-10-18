from django.test import TestCase

class RedirectTests(TestCase):
    fixtures = ["eric", "test_data"]


    def test_proper_url_no_slash(self):
        r = self.client.get('/docs/pip')
        # This is triggered by Django, so its a 301, basically just APPEND_SLASH
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r._headers['location'], ('Location', 'http://testserver/docs/pip/'))
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

    def test_inproper_subdomain(self):
        r = self.client.get('/en/', HTTP_HOST = 'pip.readthedocs.org')
        self.assertEqual(r.status_code, 404)

    def test_proper_subdomain_and_url(self):
        r = self.client.get('/en/latest/', HTTP_HOST = 'pip.readthedocs.org')
        self.assertEqual(r.status_code, 200)
