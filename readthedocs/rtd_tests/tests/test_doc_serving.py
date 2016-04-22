import django_dynamic_fixture as fixture

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.models import Project


@override_settings(
    USE_SUBDOMAIN=False, PUBLIC_DOMAIN='public.readthedocs.org', DEBUG=False
)
class TestPrivateDocs(TestCase):

    def setUp(self):
        self.eric = fixture.get(User, username='eric')
        self.eric.set_password('eric')
        self.eric.save()
        self.public = fixture.get(Project, slug='public', main_language_project=None)
        self.private = fixture.get(
            Project, slug='private', privacy_level='private',
            version_privacy_level='private', users=[self.eric],
        )

    @override_settings(
        PYTHON_MEDIA=False, SERVE_PUBLIC_DOCS=False
    )
    def test_private_nginx_serving(self):
        self.client.login(username='eric', password='eric')
        r = self.client.get('/docs/private/en/latest/usage.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r._headers['x-accel-redirect'][1], '/private_web_root/private/en/latest/usage.html'
        )

        self.client.logout()
        r = self.client.get('/docs/private/en/latest/usage.html')
        self.assertEqual(r.status_code, 401)

    @override_settings(
        PYTHON_MEDIA=False, SERVE_PUBLIC_DOCS=True
    )
    def test_public_nginx_doc_serving(self):
        self.client.login(username='eric', password='eric')
        r = self.client.get('/docs/private/en/latest/usage.html')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r._headers['x-accel-redirect'][1], '/private_web_root/private/en/latest/usage.html'
        )

        self.client.logout()
        r = self.client.get('/docs/private/en/latest/usage.html')
        self.assertEqual(r.status_code, 401)

    @override_settings(
        PYTHON_MEDIA=True, SERVE_PUBLIC_DOCS=False
    )
    def test_private_python_media_serving(self):
        self.client.login(username='eric', password='eric')
        r = self.client.get('/docs/private/en/latest/usage.html')

        self.client.logout()
        r = self.client.get('/docs/private/en/latest/usage.html')
        self.assertEqual(r.status_code, 401)

    @override_settings(
        PYTHON_MEDIA=True, SERVE_PUBLIC_DOCS=True
    )
    def test_public_python_doc_serving(self):
        self.client.login(username='eric', password='eric')
        r = self.client.get('/docs/private/en/latest/usage.html')
        self.assertEqual(r.status_code, 404)

        self.client.logout()
        r = self.client.get('/docs/private/en/latest/usage.html')
        self.assertEqual(r.status_code, 401)
