from __future__ import absolute_import
from __future__ import print_function
import re

from allauth.socialaccount.models import SocialAccount
from builtins import object
from django.contrib.admindocs.views import extract_views_from_urlpatterns
from django.test import TestCase
from django.core.urlresolvers import reverse
from django_dynamic_fixture import get
import mock
from taggit.models import Tag

from readthedocs.builds.models import Build, BuildCommandResult
from readthedocs.core.utils.tasks import TaskNoPermission
from readthedocs.integrations.models import HttpExchange, Integration
from readthedocs.projects.models import Project, Domain
from readthedocs.oauth.models import RemoteRepository, RemoteOrganization
from readthedocs.rtd_tests.utils import create_user


class URLAccessMixin(object):

    default_kwargs = {}
    response_data = {}
    request_data = {}
    context_data = []
    default_status_code = 200

    def login(self):
        raise NotImplementedError

    def is_admin(self):
        raise NotImplementedError

    def get_url_path_ctx(self):
        return {}

    def assertResponse(self, path, name=None, method=None, data=None, **kwargs):
        self.login()
        if method is None:
            method = self.client.get
        if data is None:
            data = {}

        # Get view specific query data
        request_data = self.request_data.get(path, {}).copy()
        if not request_data:
            request_data = self.request_data.get(name, {}).copy()

        if 'data' in request_data:
            data.update(request_data['data'])
            del request_data['data']

        response = method(path, data=data)

        # Get response specific test data
        response_data = self.response_data.get(path, {}).copy()
        if not response_data:
            response_data = self.response_data.get(name, {}).copy()

        response_attrs = {
            'status_code': response_data.pop('status_code', self.default_status_code),
        }
        response_attrs.update(kwargs)
        response_attrs.update(response_data)
        if self.context_data and getattr(response, 'context'):
            self._test_context(response)
        for (key, val) in list(response_attrs.items()):
            resp_val = getattr(response, key)
            self.assertEqual(
                resp_val,
                val,
                ('Attribute mismatch for view {view} ({path}): '
                 '{key} != {expected} (got {value})'
                 .format(view=name, path=path, key=key, expected=val,
                         value=resp_val))
            )
        return response

    def _test_context(self, response):
        """
        Allow for testing the template context rendered to verify no data leakage.

        Usage::

            def setUp(self):
                self.context_data.append(self.pip)
        """

        for key in list(response.context.keys()):
            obj = response.context[key]
            for not_obj in self.context_data:
                if isinstance(obj, list) or isinstance(obj, set) or isinstance(obj, tuple):
                    self.assertNotIn(not_obj, obj)
                    print("%s not in %s" % (not_obj, obj))
                else:
                    self.assertNotEqual(not_obj, obj)
                    print("%s is not %s" % (not_obj, obj))

    def _test_url(self, urlpatterns):
        deconstructed_urls = extract_views_from_urlpatterns(urlpatterns)
        added_kwargs = {}

        # we need to format urls with proper ids
        url_ctx = self.get_url_path_ctx()
        if url_ctx:
            self.response_data = {
                url.format(**url_ctx): data for url, data in self.response_data.items()}

        for (view, regex, namespace, name) in deconstructed_urls:
            request_data = self.request_data.get(name, {}).copy()
            for key in list(re.compile(regex).groupindex.keys()):
                if key in list(request_data.keys()):
                    added_kwargs[key] = request_data[key]
                    continue
                if key not in self.default_kwargs:
                    raise Exception('URL argument not in test kwargs. Please add `%s`' % key)
                added_kwargs[key] = self.default_kwargs[key]
            path = reverse(name, kwargs=added_kwargs)
            self.assertResponse(path=path, name=name)
            added_kwargs = {}

    def setUp(self):
        # Previous Fixtures
        self.owner = create_user(username='owner', password='test')
        self.tester = create_user(username='tester', password='test')
        self.pip = get(Project, slug='pip', users=[self.owner],
                       privacy_level='public', main_language_project=None)
        self.private = get(Project, slug='private', privacy_level='private',
                           main_language_project=None)


class ProjectMixin(URLAccessMixin):

    def setUp(self):
        super(ProjectMixin, self).setUp()
        self.build = get(Build, project=self.pip)
        self.tag = get(Tag, slug='coolness')
        self.subproject = get(Project, slug='sub', language='ja',
                              users=[self.owner], main_language_project=None)
        self.pip.add_subproject(self.subproject)
        self.pip.translations.add(self.subproject)
        self.integration = get(Integration, project=self.pip, provider_data='')
        # For whatever reason, fixtures hates JSONField
        self.webhook_exchange = HttpExchange.objects.create(
            related_object=self.integration,
            request_headers='{"foo": "bar"}',
            response_headers='{"foo": "bar"}',
            status_code=200,
        )
        self.domain = get(Domain, url='http://docs.foobar.com', project=self.pip)
        self.default_kwargs = {
            'project_slug': self.pip.slug,
            'subproject_slug': self.subproject.slug,
            'version_slug': self.pip.versions.all()[0].slug,
            'filename': 'index.html',
            'type_': 'pdf',
            'tag': self.tag.slug,
            'child_slug': self.subproject.slug,
            'build_pk': self.build.pk,
            'domain_pk': self.domain.pk,
            'integration_pk': self.integration.pk,
            'exchange_pk': self.webhook_exchange.pk,
        }


class PublicProjectMixin(ProjectMixin):

    request_data = {
        '/projects/search/autocomplete/': {'data': {'term': 'pip'}},
        '/projects/autocomplete/version/pip/': {'data': {'term': 'pip'}},
        '/projects/pip/autocomplete/file/': {'data': {'term': 'pip'}},
    }
    response_data = {
        # Public
        '/projects/pip/downloads/pdf/latest/': {'status_code': 302},
        '/projects/pip/badge/': {'status_code': 200},
    }

    def test_public_urls(self):
        from readthedocs.projects.urls.public import urlpatterns
        self._test_url(urlpatterns)


class PrivateProjectMixin(ProjectMixin):

    def test_private_urls(self):
        from readthedocs.projects.urls.private import urlpatterns
        self._test_url(urlpatterns)

# ## Public Project Testing ###


class PublicProjectAdminAccessTest(PublicProjectMixin, TestCase):

    def login(self):
        return self.client.login(username='owner', password='test')

    def is_admin(self):
        return True


class PublicProjectUserAccessTest(PublicProjectMixin, TestCase):

    def login(self):
        return self.client.login(username='tester', password='test')

    def is_admin(self):
        return False


class PublicProjectUnauthAccessTest(PublicProjectMixin, TestCase):

    def login(self):
        pass

    def is_admin(self):
        return False

# ## Private Project Testing ###


class PrivateProjectAdminAccessTest(PrivateProjectMixin, TestCase):

    response_data = {
        # Places where we 302 on success -- These delete pages should probably be 405'ing
        '/dashboard/import/manual/demo/': {'status_code': 302},
        '/dashboard/pip/': {'status_code': 302},
        '/dashboard/pip/subprojects/delete/sub/': {'status_code': 302},
        '/dashboard/pip/translations/delete/sub/': {'status_code': 302},

        # This depends on an inactive project
        '/dashboard/pip/version/latest/delete_html/': {'status_code': 400},

        # 405's where we should be POST'ing
        '/dashboard/pip/users/delete/': {'status_code': 405},
        '/dashboard/pip/notifications/delete/': {'status_code': 405},
        '/dashboard/pip/redirects/delete/': {'status_code': 405},
        '/dashboard/pip/subprojects/sub/delete/': {'status_code': 405},
        '/dashboard/pip/integrations/sync/': {'status_code': 405},
        '/dashboard/pip/integrations/{integration_id}/sync/': {'status_code': 405},
        '/dashboard/pip/integrations/{integration_id}/delete/': {'status_code': 405},
    }

    def get_url_path_ctx(self):
        return {
            'integration_id': self.integration.id,
        }

    def login(self):
        return self.client.login(username='owner', password='test')

    def is_admin(self):
        return True


class PrivateProjectUserAccessTest(PrivateProjectMixin, TestCase):

    response_data = {
        # Auth'd users can import projects, have no perms on pip
        '/dashboard/': {'status_code': 200},
        '/dashboard/import/': {'status_code': 200},
        '/dashboard/import/manual/': {'status_code': 200},
        '/dashboard/import/manual/demo/': {'status_code': 302},

        # Unauth access redirect for non-owners
        '/dashboard/pip/': {'status_code': 302},

        # 405's where we should be POST'ing
        '/dashboard/pip/users/delete/': {'status_code': 405},
        '/dashboard/pip/notifications/delete/': {'status_code': 405},
        '/dashboard/pip/redirects/delete/': {'status_code': 405},
        '/dashboard/pip/subprojects/sub/delete/': {'status_code': 405},
        '/dashboard/pip/integrations/sync/': {'status_code': 405},
        '/dashboard/pip/integrations/{integration_id}/sync/': {'status_code': 405},
        '/dashboard/pip/integrations/{integration_id}/delete/': {'status_code': 405},
    }

    # Filtered out by queryset on projects that we don't own.
    default_status_code = 404

    def get_url_path_ctx(self):
        return {
            'integration_id': self.integration.id,
        }

    def login(self):
        return self.client.login(username='tester', password='test')

    def is_admin(self):
        return False


class PrivateProjectUnauthAccessTest(PrivateProjectMixin, TestCase):

    # Auth protected
    default_status_code = 302

    def login(self):
        pass

    def is_admin(self):
        return False


class APIMixin(URLAccessMixin):

    def setUp(self):
        super(APIMixin, self).setUp()
        self.build = get(Build, project=self.pip)
        self.build_command_result = get(BuildCommandResult, project=self.pip)
        self.domain = get(Domain, url='http://docs.foobar.com', project=self.pip)
        self.social_account = get(SocialAccount)
        self.remote_org = get(RemoteOrganization)
        self.remote_repo = get(RemoteRepository, organization=self.remote_org)
        self.integration = get(Integration, project=self.pip, provider_data='')
        self.default_kwargs = {
            'project_slug': self.pip.slug,
            'version_slug': self.pip.versions.all()[0].slug,
            'format': 'json',
            'pk': self.pip.pk,
            'task_id': 'Nope',
        }
        self.request_data = {
            'build-detail': {'pk': self.build.pk},
            'buildcommandresult-detail': {'pk': self.build_command_result.pk},
            'version-detail': {'pk': self.pip.versions.all()[0].pk},
            'domain-detail': {'pk': self.domain.pk},
            'footer_html': {'data': {'project': 'pip', 'version': 'latest', 'page': 'index'}},
            'remoteorganization-detail': {'pk': self.remote_org.pk},
            'remoterepository-detail': {'pk': self.remote_repo.pk},
            'remoteaccount-detail': {'pk': self.social_account.pk},
            'api_webhook': {'integration_pk': self.integration.pk},
        }
        self.response_data = {
            'project-sync-versions': {'status_code': 403},
            'project-token': {'status_code': 403},
            'emailhook-list': {'status_code': 403},
            'emailhook-detail': {'status_code': 403},
            'embed': {'status_code': 400},
            'docurl': {'status_code': 400},
            'cname': {'status_code': 400},
            'index_search': {'status_code': 403},
            'api_search': {'status_code': 400},
            'api_project_search': {'status_code': 400},
            'api_section_search': {'status_code': 400},
            'api_sync_remote_repositories': {'status_code': 403},
            'api_webhook': {'status_code': 405},
            'api_webhook_github': {'status_code': 405},
            'api_webhook_gitlab': {'status_code': 405},
            'api_webhook_bitbucket': {'status_code': 405},
            'api_webhook_generic': {'status_code': 403},
            'remoteorganization-detail': {'status_code': 404},
            'remoterepository-detail': {'status_code': 404},
            'remoteaccount-detail': {'status_code': 404},
        }


class APIUnauthAccessTest(APIMixin, TestCase):

    @mock.patch('readthedocs.restapi.views.task_views.get_public_task_data')
    def test_api_urls(self, get_public_task_data):
        from readthedocs.restapi.urls import urlpatterns
        get_public_task_data.side_effect = TaskNoPermission('Nope')
        self._test_url(urlpatterns)

    def login(self):
        pass

    def is_admin(self):
        return False
