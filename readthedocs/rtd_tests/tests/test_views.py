# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import mock
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.six.moves.urllib.parse import urlsplit
from django_dynamic_fixture import get, new

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Build
from readthedocs.core.permissions import AdminPermission
from readthedocs.projects.forms import UpdateProjectForm
from readthedocs.projects.models import ImportedFile, Project

class Testmaker(TestCase):

    def setUp(self):
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()

    def test_imported_docs(self):
        # Test Import
        self.client.login(username='eric', password='test')
        user = User.objects.get(username='eric')
        r = self.client.get('/dashboard/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/dashboard/import/manual/', {})
        self.assertEqual(r.status_code, 200)
        form = UpdateProjectForm(
            data={
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
            },
            user=user,
        )
        _ = form.save()
        _ = Project.objects.get(slug='django-kong')

        r = self.client.get('/dashboard/django-kong/versions/', {})
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/builds/')
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

    def test_projects_manage(self):
        response = self.client.get('/dashboard/pip/')
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
        # This URL doesn't exist anymore, 404
        response = self.client.get(
            '/dashboard/pip/subprojects/delete/a-subproject/',
        )
        self.assertEqual(response.status_code, 404)
        # New URL
        response = self.client.get(
            '/dashboard/pip/subprojects/a-subproject/delete/',
        )
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

    def test_project_notifications_delete(self):
        response = self.client.get('/dashboard/pip/notifications/delete/')
        self.assertRedirectToLogin(response)

    def test_project_translations(self):
        response = self.client.get('/dashboard/pip/translations/')
        self.assertRedirectToLogin(response)

    def test_project_translations_delete(self):
        response = self.client.get(
            '/dashboard/pip/translations/delete/a-translation/'
        )
        self.assertRedirectToLogin(response)

    def test_project_redirects(self):
        response = self.client.get('/dashboard/pip/redirects/')
        self.assertRedirectToLogin(response)

    def test_project_redirects_delete(self):
        response = self.client.get('/dashboard/pip/redirects/delete/')
        self.assertRedirectToLogin(response)


class RandomPageTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')
        self.pip_version = self.pip.versions.all()[0]
        ImportedFile.objects.create(
            project=self.pip,
            version=self.pip_version,
            name='File',
            slug='file',
            path='file.html',
            md5='abcdef',
            commit='1234567890abcdef',
        )

    def test_random_page_view_redirects(self):
        response = self.client.get('/random/')
        self.assertEqual(response.status_code, 302)

    def test_takes_project_slug(self):
        response = self.client.get('/random/pip/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('pip' in response['Location'])

    def test_404_for_unknown_project(self):
        response = self.client.get('/random/not-existent/')
        self.assertEqual(response.status_code, 404)

    def test_404_for_with_no_imported_files(self):
        ImportedFile.objects.all().delete()
        response = self.client.get('/random/pip/')
        self.assertEqual(response.status_code, 404)


class SubprojectViewTests(TestCase):

    def setUp(self):
        self.user = new(User, username='test')
        self.user.set_password('test')
        self.user.save()

        self.project = get(Project, slug='my-mainproject')
        self.subproject = get(Project, slug='my-subproject')
        self.project.add_subproject(self.subproject)

        self.client.login(username='test', password='test')

    def test_deny_delete_for_non_project_admins(self):
        response = self.client.get(
            '/dashboard/my-mainproject/subprojects/delete/my-subproject/'
        )
        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            self.subproject in
            [r.child for r in self.project.subprojects.all()]
        )

    def test_admins_can_delete_subprojects(self):
        self.project.users.add(self.user)
        self.subproject.users.add(self.user)

        # URL doesn't exist anymore, 404
        response = self.client.get(
            '/dashboard/my-mainproject/subprojects/delete/my-subproject/',
        )
        self.assertEqual(response.status_code, 404)
        # This URL still doesn't accept GET, 405
        response = self.client.get(
            '/dashboard/my-mainproject/subprojects/my-subproject/delete/',
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            self.subproject in
            [r.child for r in self.project.subprojects.all()]
        )
        # Test POST
        response = self.client.post(
            '/dashboard/my-mainproject/subprojects/my-subproject/delete/',
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            self.subproject not in
            [r.child for r in self.project.subprojects.all()]
        )

    def test_project_admins_can_delete_subprojects_that_they_are_not_admin_of(
            self
    ):
        self.project.users.add(self.user)
        self.assertFalse(AdminPermission.is_admin(self.user, self.subproject))

        response = self.client.post(
            '/dashboard/my-mainproject/subprojects/my-subproject/delete/',
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            self.subproject not in
            [r.child for r in self.project.subprojects.all()]
        )


class BuildViewTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')

    @mock.patch('readthedocs.projects.tasks.update_docs_task')
    def test_build_redirect(self, mock):
        r = self.client.post('/projects/pip/builds/', {'version_slug': '0.8.1'})
        build = Build.objects.filter(project__slug='pip').latest()
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r._headers['location'][1],
            '/projects/pip/builds/%s/' % build.pk,
        )
