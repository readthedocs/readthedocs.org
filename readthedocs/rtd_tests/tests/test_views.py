from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.six.moves.urllib.parse import urlsplit

from builds.constants import LATEST
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
            'default_version': LATEST,
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


class PrivateViewsAreProtectedTests(TestCase):
    fixtures = ['eric', 'test_data']

    def assertRedirectToLogin(self, response):
        self.assertEqual(response.status_code, 302)
        url = response['Location']
        e_scheme, e_netloc, e_path, e_query, e_fragment = urlsplit(url)
        self.assertEqual(e_path, reverse('account_login'))

    def test_dashboard(self):
        response = self.client.get('/dashboard/')
        self.assertRedirectToLogin(response)

    def test_import_wizard_start(self):
        response = self.client.get('/dashboard/import/')
        self.assertRedirectToLogin(response)

    def test_import_wizard_manual(self):
        response = self.client.get('/dashboard/import/manual/')
        self.assertRedirectToLogin(response)

    def test_import_wizard_demo(self):
        response = self.client.get('/dashboard/import/manual/demo/')
        self.assertRedirectToLogin(response)

    def test_import_github(self):
        response = self.client.get('/dashboard/import/github/')
        self.assertRedirectToLogin(response)

        response = self.client.get('/dashboard/import/github/sync/')
        self.assertRedirectToLogin(response)

    def test_import_bitbucket(self):
        response = self.client.get('/dashboard/import/bitbucket/')
        self.assertRedirectToLogin(response)

        response = self.client.get('/dashboard/import/bitbucket/sync/')
        self.assertRedirectToLogin(response)

    def test_projects_manage(self):
        response = self.client.get('/dashboard/pip/')
        self.assertRedirectToLogin(response)

    def test_alias_manage(self):
        response = self.client.get('/dashboard/pip/alias/')
        self.assertRedirectToLogin(response)

    def test_comments_moderation(self):
        response = self.client.get('/dashboard/pip/comments_moderation/')
        self.assertRedirectToLogin(response)

    def test_edit(self):
        response = self.client.get('/dashboard/pip/edit/')
        self.assertRedirectToLogin(response)

    def test_advanced(self):
        response = self.client.get('/dashboard/pip/advanced/')
        self.assertRedirectToLogin(response)

    def test_version_delete_html(self):
        response = self.client.get('/dashboard/pip/version/0.8.1/delete_html/')
        self.assertRedirectToLogin(response)

    def test_version_detail(self):
        response = self.client.get('/dashboard/pip/version/0.8.1/')
        self.assertRedirectToLogin(response)

    def test_versions(self):
        response = self.client.get('/dashboard/pip/versions/')
        self.assertRedirectToLogin(response)

    def test_project_delete(self):
        response = self.client.get('/dashboard/pip/delete/')
        self.assertRedirectToLogin(response)

    def test_subprojects_delete(self):
        response = self.client.get(
            '/dashboard/pip/subprojects/delete/a-subproject/')
        self.assertRedirectToLogin(response)

    def test_subprojects(self):
        response = self.client.get('/dashboard/pip/subprojects/')
        self.assertRedirectToLogin(response)

    def test_project_users(self):
        response = self.client.get('/dashboard/pip/users/')
        self.assertRedirectToLogin(response)

    def test_project_users_delete(self):
        response = self.client.get('/dashboard/pip/users/delete/')
        self.assertRedirectToLogin(response)

    def test_project_notifications(self):
        response = self.client.get('/dashboard/pip/notifications/')
        self.assertRedirectToLogin(response)

    def test_project_comments(self):
        response = self.client.get('/dashboard/pip/comments/')
        self.assertRedirectToLogin(response)

    def test_project_notifications_delete(self):
        response = self.client.get('/dashboard/pip/notifications/delete/')
        self.assertRedirectToLogin(response)

    def test_project_translations(self):
        response = self.client.get('/dashboard/pip/translations/')
        self.assertRedirectToLogin(response)

    def test_project_translations_delete(self):
        response = self.client.get('/dashboard/pip/translations/delete/a-translation/')
        self.assertRedirectToLogin(response)

    def test_project_redirects(self):
        response = self.client.get('/dashboard/pip/redirects/')
        self.assertRedirectToLogin(response)

    def test_project_redirects_delete(self):
        response = self.client.get('/dashboard/pip/redirects/delete/')
        self.assertRedirectToLogin(response)
