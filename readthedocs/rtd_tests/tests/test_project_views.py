from __future__ import absolute_import
from datetime import timedelta


from mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.messages import constants as message_const
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic.base import ContextMixin
from django.utils import timezone
from django_dynamic_fixture import get, new

import six

from readthedocs.builds.models import Build, Version
from readthedocs.rtd_tests.base import (WizardTestCase, MockBuildTestCase,
                                        RequestFactoryTestMixin)
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.exceptions import ProjectSpamError
from readthedocs.projects.models import Project, Domain
from readthedocs.projects.views.private import ImportWizardView
from readthedocs.projects.views.mixins import ProjectRelationMixin
from readthedocs.projects import tasks


@patch('readthedocs.projects.views.private.trigger_build', lambda x: None)
class TestProfileMiddleware(RequestFactoryTestMixin, TestCase):

    wizard_class_slug = 'import_wizard_view'
    url = '/dashboard/import/manual/'

    def setUp(self):
        super(TestProfileMiddleware, self).setUp()
        data = {
            'basics': {
                'name': 'foobar',
                'repo': 'http://example.com/foobar',
                'repo_type': 'git',
            },
            'extra': {
                'description': 'Describe foobar',
                'language': 'en',
                'documentation_type': 'sphinx',
            },
        }
        self.data = {}
        for key in data:
            self.data.update({('{0}-{1}'.format(key, k), v)
                              for (k, v) in list(data[key].items())})
        self.data['{0}-current_step'.format(self.wizard_class_slug)] = 'extra'

    def test_profile_middleware_no_profile(self):
        """User without profile and isn't banned"""
        req = self.request('/projects/import', method='post', data=self.data)
        req.user = get(User, profile=None)
        resp = ImportWizardView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/projects/foobar/')

    @patch('readthedocs.projects.views.private.ProjectBasicsForm.clean')
    def test_profile_middleware_spam(self, form):
        """User will be banned"""
        form.side_effect = ProjectSpamError
        req = self.request('/projects/import', method='post', data=self.data)
        req.user = get(User)
        resp = ImportWizardView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/')
        self.assertTrue(req.user.profile.banned)

    def test_profile_middleware_banned(self):
        """User is banned"""
        req = self.request('/projects/import', method='post', data=self.data)
        req.user = get(User)
        req.user.profile.banned = True
        req.user.profile.save()
        self.assertTrue(req.user.profile.banned)
        resp = ImportWizardView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/')


class TestBasicsForm(WizardTestCase):

    wizard_class_slug = 'import_wizard_view'
    wizard_class = ImportWizardView
    url = '/dashboard/import/manual/'

    def setUp(self):
        self.user = get(User)
        self.step_data['basics'] = {
            'name': 'foobar',
            'repo': 'http://example.com/foobar',
            'repo_type': 'git',
        }

    def tearDown(self):
        Project.objects.filter(slug='foobar').delete()

    def request(self, *args, **kwargs):
        kwargs['user'] = self.user
        return super(TestBasicsForm, self).request(*args, **kwargs)

    def test_form_pass(self):
        """Only submit the basics"""
        resp = self.post_step('basics')
        self.assertIsInstance(resp, HttpResponseRedirect)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/projects/foobar/')

        proj = Project.objects.get(name='foobar')
        self.assertIsNotNone(proj)
        for (key, val) in list(self.step_data['basics'].items()):
            self.assertEqual(getattr(proj, key), val)
        self.assertEqual(proj.documentation_type, 'sphinx')

    def test_remote_repository_is_added(self):
        remote_repo = get(RemoteRepository, users=[self.user])
        self.step_data['basics']['remote_repository'] = remote_repo.pk
        resp = self.post_step('basics')
        self.assertIsInstance(resp, HttpResponseRedirect)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/projects/foobar/')

        proj = Project.objects.get(name='foobar')
        self.assertIsNotNone(proj)
        self.assertEqual(proj.remote_repository, remote_repo)

    def test_remote_repository_is_not_added_for_wrong_user(self):
        user = get(User)
        remote_repo = get(RemoteRepository, users=[user])
        self.step_data['basics']['remote_repository'] = remote_repo.pk
        resp = self.post_step('basics')
        self.assertWizardFailure(resp, 'remote_repository')

    def test_form_missing(self):
        """Submit form with missing data, expect to get failures"""
        self.step_data['basics'] = {'advanced': True}
        resp = self.post_step('basics')
        self.assertWizardFailure(resp, 'name')
        self.assertWizardFailure(resp, 'repo_type')


class TestAdvancedForm(TestBasicsForm):

    def setUp(self):
        super(TestAdvancedForm, self).setUp()
        self.step_data['basics']['advanced'] = True
        self.step_data['extra'] = {
            'description': 'Describe foobar',
            'language': 'en',
            'documentation_type': 'sphinx',
            'tags': 'foo, bar, baz',
        }

    def test_form_pass(self):
        """Test all forms pass validation"""
        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra', session=list(resp._request.session.items()))
        self.assertIsInstance(resp, HttpResponseRedirect)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/projects/foobar/')

        proj = Project.objects.get(name='foobar')
        self.assertIsNotNone(proj)
        data = self.step_data['basics']
        del data['advanced']
        del self.step_data['extra']['tags']
        six.assertCountEqual(
            self,
            [tag.name for tag in proj.tags.all()],
            [u'bar', u'baz', u'foo'])
        data.update(self.step_data['extra'])
        for (key, val) in list(data.items()):
            self.assertEqual(getattr(proj, key), val)

    def test_form_missing_extra(self):
        """Submit extra form with missing data, expect to get failures"""
        # Remove extra data to trigger validation errors
        self.step_data['extra'] = {}

        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra', session=list(resp._request.session.items()))

        self.assertWizardFailure(resp, 'language')
        self.assertWizardFailure(resp, 'documentation_type')

    def test_remote_repository_is_added(self):
        remote_repo = get(RemoteRepository, users=[self.user])
        self.step_data['basics']['remote_repository'] = remote_repo.pk
        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra', session=list(resp._request.session.items()))
        self.assertIsInstance(resp, HttpResponseRedirect)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/projects/foobar/')

        proj = Project.objects.get(name='foobar')
        self.assertIsNotNone(proj)
        self.assertEqual(proj.remote_repository, remote_repo)

    @patch('readthedocs.projects.views.private.ProjectExtraForm.clean_description',
           create=True)
    def test_form_spam(self, mocked_validator):
        """Don't add project on a spammy description"""
        self.user.date_joined = timezone.now() - timedelta(days=365)
        self.user.save()
        mocked_validator.side_effect = ProjectSpamError

        with self.assertRaises(Project.DoesNotExist):
            proj = Project.objects.get(name='foobar')

        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra', session=list(resp._request.session.items()))
        self.assertIsInstance(resp, HttpResponseRedirect)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/')

        with self.assertRaises(Project.DoesNotExist):
            proj = Project.objects.get(name='foobar')
        self.assertFalse(self.user.profile.banned)

    @patch('readthedocs.projects.views.private.ProjectExtraForm.clean_description',
           create=True)
    def test_form_spam_ban_user(self, mocked_validator):
        """Don't add spam and ban new user"""
        self.user.date_joined = timezone.now()
        self.user.save()
        mocked_validator.side_effect = ProjectSpamError

        with self.assertRaises(Project.DoesNotExist):
            proj = Project.objects.get(name='foobar')

        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra', session=list(resp._request.session.items()))
        self.assertIsInstance(resp, HttpResponseRedirect)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/')

        with self.assertRaises(Project.DoesNotExist):
            proj = Project.objects.get(name='foobar')
        self.assertTrue(self.user.profile.banned)


class TestImportDemoView(MockBuildTestCase):
    """Test project import demo view"""

    fixtures = ['test_data', 'eric']

    def setUp(self):
        self.client.login(username='eric', password='test')

    def test_import_demo_pass(self):
        resp = self.client.get('/dashboard/import/manual/demo/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/projects/eric-demo/')
        resp_redir = self.client.get(resp['Location'])
        self.assertEqual(resp_redir.status_code, 200)
        messages = list(resp_redir.context['messages'])
        self.assertEqual(messages[0].level, message_const.SUCCESS)

    def test_import_demo_already_imported(self):
        """Import demo project multiple times, expect failure 2nd post"""
        self.test_import_demo_pass()
        project = Project.objects.get(slug='eric-demo')

        resp = self.client.get('/dashboard/import/manual/demo/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/projects/eric-demo/')

        resp_redir = self.client.get(resp['Location'])
        self.assertEqual(resp_redir.status_code, 200)
        messages = list(resp_redir.context['messages'])
        self.assertEqual(messages[0].level, message_const.SUCCESS)

        self.assertEqual(project,
                         Project.objects.get(slug='eric-demo'))

    def test_import_demo_another_user_imported(self):
        """Import demo project after another user, expect success"""
        self.test_import_demo_pass()
        project = Project.objects.get(slug='eric-demo')

        self.client.logout()
        self.client.login(username='test', password='test')
        resp = self.client.get('/dashboard/import/manual/demo/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/projects/test-demo/')

        resp_redir = self.client.get(resp['Location'])
        self.assertEqual(resp_redir.status_code, 200)
        messages = list(resp_redir.context['messages'])
        self.assertEqual(messages[0].level, message_const.SUCCESS)

    def test_import_demo_imported_renamed(self):
        """If the demo project is renamed, don't import another"""
        self.test_import_demo_pass()
        project = Project.objects.get(slug='eric-demo')
        project.name = 'eric-demo-foobar'
        project.save()

        resp = self.client.get('/dashboard/import/manual/demo/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/projects/eric-demo/')

        resp_redir = self.client.get(resp['Location'])
        self.assertEqual(resp_redir.status_code, 200)
        messages = list(resp_redir.context['messages'])
        self.assertEqual(messages[0].level, message_const.SUCCESS)
        self.assertRegexpMatches(messages[0].message,
                                 r'already imported')

        self.assertEqual(project,
                         Project.objects.get(slug='eric-demo'))

    def test_import_demo_imported_duplicate(self):
        """If a project exists with same name, expect a failure importing demo

        This should be edge case, user would have to import a project (not the
        demo project), named user-demo, and then manually enter the demo import
        URL, as the onboarding isn't shown when projects > 0
        """
        self.test_import_demo_pass()
        project = Project.objects.get(slug='eric-demo')
        project.repo = 'file:///foobar'
        project.save()

        resp = self.client.get('/dashboard/import/manual/demo/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/dashboard/')

        resp_redir = self.client.get(resp['Location'])
        self.assertEqual(resp_redir.status_code, 200)
        messages = list(resp_redir.context['messages'])
        self.assertEqual(messages[0].level, message_const.ERROR)
        self.assertRegexpMatches(messages[0].message,
                                 r'There was a problem')

        self.assertEqual(project,
                         Project.objects.get(slug='eric-demo'))


class TestPrivateViews(MockBuildTestCase):
    def setUp(self):
        self.user = new(User, username='eric')
        self.user.set_password('test')
        self.user.save()
        self.client.login(username='eric', password='test')

    def test_versions_page(self):
        pip = get(Project, slug='pip', users=[self.user])
        pip.versions.create(verbose_name='1.0')

        response = self.client.get('/projects/pip/versions/')
        self.assertEqual(response.status_code, 200)

        # Test if the versions page works with a version that contains a slash.
        # That broke in the past, see issue #1176.
        pip.versions.create(verbose_name='1.0/with-slash')

        response = self.client.get('/projects/pip/versions/')
        self.assertEqual(response.status_code, 200)

    def test_delete_project(self):
        project = get(Project, slug='pip', users=[self.user])

        response = self.client.get('/dashboard/pip/delete/')
        self.assertEqual(response.status_code, 200)

        with patch('readthedocs.projects.views.private.broadcast') as broadcast:
            response = self.client.post('/dashboard/pip/delete/')
            self.assertEqual(response.status_code, 302)
            self.assertFalse(Project.objects.filter(slug='pip').exists())
            broadcast.assert_called_with(
                type='app',
                task=tasks.remove_dir,
                args=[project.doc_path])

    def test_subproject_create(self):
        project = get(Project, slug='pip', users=[self.user])
        subproject = get(Project, users=[self.user])

        with patch('readthedocs.projects.views.private.broadcast') as broadcast:
            response = self.client.post(
                '/dashboard/pip/subprojects/create/',
                data={'child': subproject.pk},
            )
            self.assertEqual(response.status_code, 302)
            broadcast.assert_called_with(
                type='app',
                task=tasks.symlink_subproject,
                args=[project.pk])


class TestPrivateMixins(MockBuildTestCase):

    def setUp(self):
        self.project = get(Project, slug='kong')
        self.domain = get(Domain, project=self.project)

    def test_project_relation(self):
        """Class using project relation mixin class"""

        class FoobarView(ProjectRelationMixin, ContextMixin):
            model = Domain

            def get_project_queryset(self):
                # Don't test this as a view with a request.user
                return Project.objects.all()

        view = FoobarView()
        view.kwargs = {'project_slug': 'kong'}
        self.assertEqual(view.get_project(), self.project)
        self.assertEqual(view.get_queryset().first(), self.domain)
        self.assertEqual(view.get_context_data()['project'], self.project)


class TestBadges(TestCase):
    """Test a static badge asset is served for each build."""

    def setUp(self):
        self.BADGE_PATH = 'projects/badges/%s-%s.svg'
        self.project = get(Project, slug='badgey')
        self.version = Version.objects.get(project=self.project)
        self.badge_url = reverse('project_badge', args=[self.project.slug])

    def test_unknown_badge(self):
        res = self.client.get(self.badge_url, {'version': self.version.slug})
        self.assertContains(res, 'unknown')

        # Unknown project
        unknown_project_url = reverse('project_badge', args=['fake-project'])
        res = self.client.get(unknown_project_url, {'version': 'latest'})
        self.assertContains(res, 'unknown')

    def test_passing_badge(self):
        get(Build, project=self.project, version=self.version, success=True)
        res = self.client.get(self.badge_url, {'version': self.version.slug})
        self.assertContains(res, 'passing')
        self.assertEqual(res['Content-Type'], 'image/svg+xml')

    def test_failing_badge(self):
        get(Build, project=self.project, version=self.version, success=False)
        res = self.client.get(self.badge_url, {'version': self.version.slug})
        self.assertContains(res, 'failing')

    def test_plastic_failing_badge(self):
        get(Build, project=self.project, version=self.version, success=False)
        res = self.client.get(self.badge_url, {'version': self.version.slug, 'style': 'plastic'})
        self.assertContains(res, 'failing')

        # The plastic badge has slightly more rounding
        self.assertContains(res, 'rx="4"')

    def test_social_passing_badge(self):
        get(Build, project=self.project, version=self.version, success=True)
        res = self.client.get(self.badge_url, {'version': self.version.slug, 'style': 'social'})
        self.assertContains(res, 'passing')

        # The social badge (but not the other badges) has this element
        self.assertContains(res, 'rlink')


class TestTags(TestCase):
    def test_project_filtering_work_with_tags_with_space_in_name(self):
        pip = get(Project, slug='pip')
        pip.tags.add('tag with space')
        response = self.client.get('/projects/tags/tag-with-space/')
        self.assertContains(response, '"/projects/pip/"')
