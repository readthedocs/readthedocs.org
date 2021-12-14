from datetime import timedelta
from unittest import mock

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import ContextMixin
from django_dynamic_fixture import get, new

from readthedocs.builds.constants import BUILD_STATUS_DUPLICATED, EXTERNAL
from readthedocs.builds.models import Build, Version
from readthedocs.integrations.models import GenericAPIWebhook, GitHubWebhook
from readthedocs.oauth.models import RemoteRepository, RemoteRepositoryRelation
from readthedocs.organizations.models import Organization
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.exceptions import ProjectSpamError
from readthedocs.projects.models import Domain, Project, WebHook, WebHookEvent
from readthedocs.projects.views.mixins import ProjectRelationMixin
from readthedocs.projects.views.private import ImportWizardView
from readthedocs.projects.views.public import ProjectBadgeView
from readthedocs.rtd_tests.base import RequestFactoryTestMixin, WizardTestCase


@mock.patch('readthedocs.projects.tasks.update_docs_task', mock.MagicMock())
class TestProfileMiddleware(RequestFactoryTestMixin, TestCase):

    wizard_class_slug = 'import_wizard_view'
    url = '/dashboard/import/manual/'

    def setUp(self):
        super().setUp()
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
            self.data.update({('{}-{}'.format(key, k), v)
                              for (k, v) in list(data[key].items())})
        self.data['{}-current_step'.format(self.wizard_class_slug)] = 'extra'

    def test_profile_middleware_no_profile(self):
        """User without profile and isn't banned."""
        req = self.request(method='post', path='/projects/import', data=self.data)
        req.user = get(User, profile=None)
        resp = ImportWizardView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/projects/foobar/')

    @mock.patch('readthedocs.projects.views.private.ProjectBasicsForm.clean')
    def test_profile_middleware_spam(self, form):
        """User will be banned."""
        form.side_effect = ProjectSpamError
        req = self.request(method='post', path='/projects/import', data=self.data)
        req.user = get(User)
        resp = ImportWizardView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/')
        self.assertTrue(req.user.profile.banned)

    def test_profile_middleware_banned(self):
        """User is banned."""
        req = self.request(method='post', path='/projects/import', data=self.data)
        req.user = get(User)
        req.user.profile.banned = True
        req.user.profile.save()
        self.assertTrue(req.user.profile.banned)
        resp = ImportWizardView.as_view()(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/')


@mock.patch('readthedocs.projects.tasks.update_docs_task', mock.MagicMock())
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
        return super().request(*args, **kwargs)

    def test_form_import_from_remote_repo(self):
        self.client.force_login(self.user)

        data = {
            'name': 'pipdocs',
            'repo': 'https://github.com/fail/sauce',
            'repo_type': 'git',
            'remote_repository': '1234',
            'default_branch': 'main',
        }
        resp = self.client.post(
            '/dashboard/import/',
            data,
        )
        self.assertEqual(resp.status_code, 200)

        # The form is filled with the previous information
        self.assertEqual(
            resp.context['form'].initial,
            data,
        )

    def test_form_pass(self):
        """Only submit the basics."""
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
        remote_repo = get(RemoteRepository)
        socialaccount = get(SocialAccount, user=self.user)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.user,
            account=socialaccount
        )
        self.step_data['basics']['remote_repository'] = remote_repo.pk
        resp = self.post_step('basics')
        self.assertIsInstance(resp, HttpResponseRedirect)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/projects/foobar/')

        proj = Project.objects.get(name='foobar')
        self.assertIsNotNone(proj)
        self.assertEqual(proj.remote_repository, remote_repo)

    def test_remote_repository_invalid_type(self):
        self.step_data['basics']['remote_repository'] = 'Invalid id'
        resp = self.post_step('basics')
        self.assertEqual(resp.status_code, 200)
        form = resp.context_data['form']
        self.assertIn('remote_repository', form.errors)

    def test_remote_repository_invalid_id(self):
        self.step_data['basics']['remote_repository'] = 9
        resp = self.post_step('basics')
        self.assertEqual(resp.status_code, 200)
        form = resp.context_data['form']
        self.assertIn('remote_repository', form.errors)

    def test_remote_repository_is_not_added_for_wrong_user(self):
        user = get(User)
        remote_repo = get(RemoteRepository)
        socialaccount = get(SocialAccount, user=user)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=user,
            account=socialaccount
        )
        self.step_data['basics']['remote_repository'] = remote_repo.pk
        resp = self.post_step('basics')
        self.assertWizardFailure(resp, 'remote_repository')

    def test_form_missing(self):
        """Submit form with missing data, expect to get failures."""
        self.step_data['basics'] = {'advanced': True}
        resp = self.post_step('basics')
        self.assertWizardFailure(resp, 'name')
        self.assertWizardFailure(resp, 'repo_type')


@mock.patch('readthedocs.projects.tasks.update_docs_task', mock.MagicMock())
class TestAdvancedForm(TestBasicsForm):

    def setUp(self):
        super().setUp()
        self.step_data['basics']['advanced'] = True
        self.step_data['extra'] = {
            'description': 'Describe foobar',
            'language': 'en',
            'documentation_type': 'sphinx',
            'tags': 'foo, bar, baz',
        }

    def test_initial_params(self):
        extra_initial = {
            'description': 'An amazing project',
            'project_url': "https://foo.bar",
        }
        basic_initial = {
            'name': 'foobar',
            'repo': 'https://github.com/foo/bar',
            'repo_type': 'git',
            'default_branch': 'main',
            'remote_repository': '',
        }
        initial = dict(**extra_initial, **basic_initial)
        self.client.force_login(self.user)

        # User selects a remote repo to import.
        resp = self.client.post(reverse('projects_import'), initial)

        # The correct initial data for the basic form is set.
        form = resp.context_data['form']
        self.assertEqual(form.initial, basic_initial)

        # User selects advanced.
        basic_initial['advanced'] = True
        step_data = {
            f'basics-{k}': v
            for k, v in basic_initial.items()
        }
        step_data[f'{self.wizard_class_slug}-current_step'] = 'basics'
        resp = self.client.post(self.url, step_data)

        # The correct initial data for the advanced form is set.
        form = resp.context_data['form']
        self.assertEqual(form.initial, extra_initial)

    def test_form_pass(self):
        """Test all forms pass validation."""
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
        self.assertCountEqual(
            [tag.name for tag in proj.tags.all()],
            ['bar', 'baz', 'foo'],
        )
        data.update(self.step_data['extra'])
        for (key, val) in list(data.items()):
            self.assertEqual(getattr(proj, key), val)

    def test_form_missing_extra(self):
        """Submit extra form with missing data, expect to get failures."""
        # Remove extra data to trigger validation errors
        self.step_data['extra'] = {}

        resp = self.post_step('basics')
        self.assertWizardResponse(resp, 'extra')
        resp = self.post_step('extra', session=list(resp._request.session.items()))

        self.assertWizardFailure(resp, 'language')
        self.assertWizardFailure(resp, 'documentation_type')

    def test_remote_repository_is_added(self):
        remote_repo = get(RemoteRepository)
        socialaccount = get(SocialAccount, user=self.user)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.user,
            account=socialaccount
        )
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

    @mock.patch(
        'readthedocs.projects.views.private.ProjectExtraForm.clean_description',
        create=True,
    )
    def test_form_spam(self, mocked_validator):
        """Don't add project on a spammy description."""
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

    @mock.patch(
        'readthedocs.projects.views.private.ProjectExtraForm.clean_description',
        create=True,
    )
    def test_form_spam_ban_user(self, mocked_validator):
        """Don't add spam and ban new user."""
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


@mock.patch('readthedocs.core.utils.trigger_build', mock.MagicMock())
class TestPublicViews(TestCase):
    def setUp(self):
        self.pip = get(Project, slug='pip', privacy_level=PUBLIC)
        self.external_version = get(
            Version,
            identifier='pr-version',
            verbose_name='pr-version',
            slug='pr-9999',
            project=self.pip,
            active=True,
            type=EXTERNAL
        )

    def test_project_detail_view_only_shows_internal_versons(self):
        url = reverse('projects_detail', args=[self.pip.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.external_version, response.context['versions'])

    def test_project_downloads_only_shows_internal_versons(self):
        url = reverse('project_downloads', args=[self.pip.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.external_version, response.context['versions'])

    def test_project_versions_only_shows_internal_versons(self):
        url = reverse('project_version_list', args=[self.pip.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.external_version, response.context['active_versions'])
        self.assertNotIn(self.external_version, response.context['inactive_versions'])


@mock.patch('readthedocs.core.utils.trigger_build', mock.MagicMock())
class TestPrivateViews(TestCase):
    def setUp(self):
        self.user = new(User, username='eric')
        self.user.set_password('test')
        self.user.save()
        self.client.login(username='eric', password='test')
        self.project = get(Project, slug='pip', users=[self.user])

    def test_versions_page(self):
        self.project.versions.create(verbose_name='1.0')

        response = self.client.get('/projects/pip/versions/')
        self.assertEqual(response.status_code, 200)

        # Test if the versions page works with a version that contains a slash.
        # That broke in the past, see issue #1176.
        self.project.versions.create(verbose_name='1.0/with-slash')

        response = self.client.get('/projects/pip/versions/')
        self.assertEqual(response.status_code, 200)

    def test_delete_project(self):
        response = self.client.get('/dashboard/pip/delete/')
        self.assertEqual(response.status_code, 200)

        # Mocked like this because the function is imported inside a class method
        # https://stackoverflow.com/a/22201798
        with mock.patch('readthedocs.projects.tasks.clean_project_resources') as clean_project_resources:
            response = self.client.post('/dashboard/pip/delete/')
            self.assertEqual(response.status_code, 302)
            self.assertFalse(Project.objects.filter(slug='pip').exists())
            clean_project_resources.assert_called_once()
            self.assertEqual(clean_project_resources.call_args[0][0].slug, self.project.slug)

    def test_delete_superproject(self):
        sub_proj = get(Project, slug='test-sub-project', users=[self.user])

        self.assertFalse(self.project.subprojects.all().exists())
        self.project.add_subproject(sub_proj)

        response = self.client.get('/dashboard/pip/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'This project <a href="/dashboard/pip/subprojects/">has subprojects</a> under it. '
            'Deleting this project will make them to become regular projects. '
            'This will break the URLs of all its subprojects and they will be served normally as other projects.',
            count=1,
            html=True,
        )

    @mock.patch('readthedocs.projects.views.private.attach_webhook')
    def test_integration_create(self, attach_webhook):
        response = self.client.post(
            reverse('projects_integrations_create', args=[self.project.slug]),
            data={
                'project': self.project.pk,
                'integration_type': GitHubWebhook.GITHUB_WEBHOOK
            },
        )
        integration = GitHubWebhook.objects.filter(project=self.project)

        self.assertTrue(integration.exists())
        self.assertEqual(response.status_code, 302)
        attach_webhook.assert_called_once_with(
            project_pk=self.project.pk,
            user_pk=self.user.pk,
            integration=integration.first()
        )

    @mock.patch('readthedocs.projects.views.private.attach_webhook')
    def test_integration_create_generic_webhook(self, attach_webhook):
        response = self.client.post(
            reverse('projects_integrations_create', args=[self.project.slug]),
            data={
                'project': self.project.pk,
                'integration_type': GenericAPIWebhook.API_WEBHOOK
            },
        )
        integration = GenericAPIWebhook.objects.filter(project=self.project)

        self.assertTrue(integration.exists())
        self.assertEqual(response.status_code, 302)
        attach_webhook.assert_not_called()

    def test_integration_webhooks_sync_no_remote_repository(self):
        self.project.has_valid_webhook = True
        self.project.save()
        integration = get(
            GitHubWebhook,
            project=self.project,
        )

        response = self.client.post(
            reverse(
                'projects_integrations_webhooks_sync',
                kwargs={
                    'project_slug': self.project.slug,
                    'integration_pk': integration.pk,
                },
            ),
        )
        self.project.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.project.has_valid_webhook)

    def test_remove_user(self):
        user = get(User, username='test')
        self.project.users.add(user)

        self.assertEqual(self.project.users.count(), 2)
        r = self.client.post(
            reverse('projects_users_delete', args=(self.project.slug,)),
            data={'username': 'test'}
        )
        self.assertTrue(r.status_code, 302)
        self.assertEqual(self.project.users.count(), 1)
        self.assertEqual(self.project.users.last().username, 'eric')

    def test_remove_own_user(self):
        user = get(User, username='test')
        self.project.users.add(user)

        self.assertEqual(self.project.users.count(), 2)
        r = self.client.post(
            reverse('projects_users_delete', args=(self.project.slug,)),
            data={'username': 'eric'}
        )
        self.assertTrue(r.status_code, 302)
        self.assertEqual(self.project.users.count(), 1)
        self.assertEqual(self.project.users.last().username, 'test')

    def test_remove_last_user(self):
        self.assertEqual(self.project.users.count(), 1)
        r = self.client.post(
            reverse('projects_users_delete', args=(self.project.slug,)),
            data={'username': 'eric'}
        )
        self.assertTrue(r.status_code, 400)
        self.assertEqual(self.project.users.count(), 1)
        self.assertEqual(self.project.users.last().username, 'eric')


@mock.patch('readthedocs.core.utils.trigger_build', mock.MagicMock())
@mock.patch('readthedocs.projects.tasks.update_docs_task', mock.MagicMock())
class TestPrivateMixins(TestCase):

    def setUp(self):
        self.project = get(Project, slug='kong')
        self.domain = get(Domain, project=self.project)

    def test_project_relation(self):
        """Class using project relation mixin class."""

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

        # Unknown version
        res = self.client.get(self.badge_url, {'version': 'fake-version'})
        self.assertContains(res, 'unknown')

    def test_badge_caching(self):
        res = self.client.get(self.badge_url, {'version': self.version.slug})
        self.assertTrue('must-revalidate' in res['Cache-Control'])
        self.assertTrue('no-cache' in res['Cache-Control'])

    def test_passing_badge(self):
        get(Build, project=self.project, version=self.version, success=True)
        res = self.client.get(self.badge_url, {'version': self.version.slug})
        self.assertContains(res, 'passing')
        self.assertEqual(res['Content-Type'], 'image/svg+xml')

    def test_ignore_duplicated_build(self):
        """Ignore builds marked as duplicate from the badge status."""
        get(
            Build,
            project=self.project,
            version=self.version,
            success=True,
        )
        get(
            Build,
            project=self.project,
            version=self.version,
            success=False,
            status=BUILD_STATUS_DUPLICATED,
        )
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

    def test_badge_redirect(self):
        # Test that a project with an underscore redirects
        badge_url = reverse('project_badge', args=['project_slug'])
        resp = self.client.get(badge_url, {'version': 'latest'})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue('project-slug' in resp['location'])

    def test_private_version(self):
        # Set version to private
        self.version.privacy_level = 'private'
        self.version.save()

        # Without a token, badge is unknown
        get(Build, project=self.project, version=self.version, success=True)
        res = self.client.get(self.badge_url, {'version': self.version.slug})
        self.assertContains(res, 'unknown')

        # With an invalid token, the badge is unknown
        res = self.client.get(
            self.badge_url,
            {
                'token': ProjectBadgeView.get_project_token('invalid-project'),
                'version': self.version.slug,
            }
        )
        self.assertContains(res, 'unknown')

        # With a valid token, the badge should work correctly
        res = self.client.get(
            self.badge_url,
            {
                'token': ProjectBadgeView.get_project_token(self.project.slug),
                'version': self.version.slug,
            }
        )
        self.assertContains(res, 'passing')


class TestTags(TestCase):

    def test_project_filtering_work_with_tags_with_space_in_name(self):
        pip = get(Project, slug='pip', privacy_level=PUBLIC)
        pip.tags.add('tag with space')
        response = self.client.get('/projects/tags/tag-with-space/')
        self.assertContains(response, '"/projects/pip/"')


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class TestWebhooksViews(TestCase):

    def setUp(self):
        self.user = get(User)
        self.project = get(Project, slug='test', users=[self.user])
        self.version = get(Version, slug='1.0', project=self.project)
        self.webhook = get(WebHook, project=self.project)
        self.client.force_login(self.user)

    def test_list(self):
        resp = self.client.get(
            reverse('projects_webhooks', args=[self.project.slug]),
        )
        self.assertEqual(resp.status_code, 200)
        queryset = resp.context['object_list']
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.webhook)

    def test_create(self):
        self.assertEqual(self.project.webhook_notifications.all().count(), 1)
        resp = self.client.post(
            reverse('projects_webhooks_create', args=[self.project.slug]),
            data = {
                'url': 'http://www.example.com/',
                'payload': '{}',
                'events': [WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.project.webhook_notifications.all().count(), 2)

    def test_update(self):
        self.assertEqual(self.project.webhook_notifications.all().count(), 1)
        self.client.post(
            reverse('projects_webhooks_edit', args=[self.project.slug, self.webhook.pk]),
            data = {
                'url': 'http://www.example.com/new',
                'payload': '{}',
                'events': [WebHookEvent.objects.get(name=WebHookEvent.BUILD_FAILED).id],
            },
        )
        self.webhook.refresh_from_db()
        self.assertEqual(self.webhook.url, 'http://www.example.com/new')
        self.assertEqual(self.project.webhook_notifications.all().count(), 1)

    def test_delete(self):
        self.assertEqual(self.project.webhook_notifications.all().count(), 1)
        self.client.post(
            reverse('projects_webhooks_delete', args=[self.project.slug, self.webhook.pk]),
        )
        self.assertEqual(self.project.webhook_notifications.all().count(), 0)


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestWebhooksViewsWithOrganizations(TestWebhooksViews):

    def setUp(self):
        super().setUp()
        self.organization = get(Organization, owners=[self.user], projects=[self.project])
