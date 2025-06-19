import re
from unittest import mock

from allauth.socialaccount.models import SocialAccount
from django.contrib.admindocs.views import extract_views_from_urlpatterns
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get
from taggit.models import Tag

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.models import (
    Build,
    BuildCommandResult,
    RegexAutomationRule,
    VersionAutomationRule,
)
from readthedocs.integrations.models import HttpExchange, Integration
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.projects.models import Domain, EnvironmentVariable, Project, WebHook
from readthedocs.redirects.models import Redirect
from readthedocs.rtd_tests.utils import create_user


class URLAccessMixin:
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

    def _test_cache_poisoning(self, path):
        # Test for cache poisoning in URLs,
        # to avoid problems like GHSA-7fcx-wwr3-99jv.
        original_path = path
        if not path.endswith("/"):
            path += "/"
        path += "lib.js"
        r = self.client.head(path)
        self.assertNotEqual(
            r.status_code,
            200,
            f"Path vulnerable to cache poisoning. path={original_path}",
        )

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

        if "data" in request_data:
            data.update(request_data["data"])
            del request_data["data"]

        response = method(path, data=data)

        # Get response specific test data
        response_data = self.response_data.get(path, {}).copy()
        if not response_data:
            response_data = self.response_data.get(name, {}).copy()

        response_attrs = {
            "status_code": response_data.pop("status_code", self.default_status_code),
        }
        response_attrs.update(kwargs)
        response_attrs.update(response_data)
        if self.context_data and getattr(response, "context"):
            self._test_context(response)
        for key, val in list(response_attrs.items()):
            resp_val = getattr(response, key)
            self.assertEqual(
                resp_val,
                val,
                (
                    "Attribute mismatch for view {view} ({path}): "
                    "{key} != {expected} (got {value})".format(
                        view=name,
                        path=path,
                        key=key,
                        expected=val,
                        value=resp_val,
                    )
                ),
            )

        self._test_cache_poisoning(path)
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
                if isinstance(obj, (list, set, tuple)):
                    self.assertNotIn(not_obj, obj)
                    print("{} not in {}".format(not_obj, obj))
                else:
                    self.assertNotEqual(not_obj, obj)
                    print("{} is not {}".format(not_obj, obj))

    def _test_url(self, urlpatterns):
        deconstructed_urls = extract_views_from_urlpatterns(urlpatterns)
        added_kwargs = {}

        # we need to format urls with proper ids
        url_ctx = self.get_url_path_ctx()
        if url_ctx:
            self.response_data = {
                url.format(**url_ctx): data for url, data in self.response_data.items()
            }

        for view, regex, namespace, name in deconstructed_urls:
            # Skip URL and views that are not named
            if not name:
                continue

            request_data = self.request_data.get(name, {}).copy()
            for key in list(re.compile(regex).groupindex.keys()):
                if key in list(request_data.keys()):
                    added_kwargs[key] = request_data[key]
                    continue
                if key not in self.default_kwargs:
                    raise Exception(
                        "URL argument not in test kwargs. Please add `%s`" % key
                    )
                added_kwargs[key] = self.default_kwargs[key]
            path = reverse(name, kwargs=added_kwargs)
            self.assertResponse(path=path, name=name)
            added_kwargs = {}

    def setUp(self):
        # Previous Fixtures
        self.owner = create_user(username="owner", password="test")
        self.tester = create_user(username="tester", password="test")
        self.pip = get(
            Project,
            slug="pip",
            users=[self.owner],
            privacy_level="public",
            main_language_project=None,
        )
        self.private = get(
            Project,
            slug="private",
            privacy_level="private",
            main_language_project=None,
        )


class ProjectMixin(URLAccessMixin):
    def setUp(self):
        super().setUp()
        self.build = get(Build, project=self.pip, version=self.pip.versions.first())
        self.tag = get(Tag, slug="coolness")
        self.subproject = get(
            Project,
            slug="sub",
            language="ja",
            users=[self.owner],
            main_language_project=None,
        )
        self.pip.add_subproject(self.subproject)
        self.pip.translations.add(self.subproject)
        self.integration = get(Integration, project=self.pip, provider_data="")
        # For whatever reason, fixtures hates JSONField
        self.integration_exchange = HttpExchange.objects.create(
            related_object=self.integration,
            request_headers={"foo": "bar"},
            response_headers={"foo": "bar"},
            status_code=200,
        )
        self.domain = get(Domain, domain="docs.foobar.com", project=self.pip)
        self.environment_variable = get(EnvironmentVariable, project=self.pip)
        self.automation_rule = RegexAutomationRule.objects.create(
            project=self.pip,
            priority=0,
            match_arg=".*",
            action=VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            version_type=BRANCH,
        )
        self.webhook = get(WebHook, project=self.pip)
        self.webhook_exchange = HttpExchange.objects.create(
            related_object=self.webhook,
            request_headers={"foo": "bar"},
            response_headers={"foo": "bar"},
            status_code=200,
        )
        self.redirect = get(
            Redirect,
            project=self.pip,
            redirect_type="sphinx_html",
        )
        self.default_kwargs = {
            "project_slug": self.pip.slug,
            "subproject_slug": self.subproject.slug,
            "version_slug": self.pip.versions.all()[0].slug,
            "filename": "index.html",
            "type_": "pdf",
            "tag": self.tag.slug,
            "child_slug": self.subproject.slug,
            "build_pk": self.build.pk,
            "domain_pk": self.domain.pk,
            "redirect_pk": self.redirect.pk,
            "integration_pk": self.integration.pk,
            "exchange_pk": self.integration_exchange.pk,
            "environmentvariable_pk": self.environment_variable.pk,
            "automation_rule_pk": self.automation_rule.pk,
            "steps": 1,
            "invalid_project_slug": "invalid_slug",
            "webhook_pk": self.webhook.pk,
            "webhook_exchange_pk": self.webhook_exchange.pk,
            "position": 0,
        }


class PublicProjectMixin(ProjectMixin):
    request_data = {
        "/projects/": {},
        "/projects/search/autocomplete/": {"data": {"term": "pip"}},
        "/projects/autocomplete/version/pip/": {"data": {"term": "pip"}},
        "/projects/pip/autocomplete/file/": {"data": {"term": "pip"}},
    }
    response_data = {
        # Public
        "/projects/": {"status_code": 301},
        "/projects/pip/downloads/": {"status_code": 302},
        "/projects/pip/downloads/pdf/latest/": {"status_code": 200},
        "/projects/pip/badge/": {"status_code": 200},
        "/projects/invalid_slug/": {"status_code": 302},
        "/projects/pip/search/": {"status_code": 302},
        "/dashboard/pip/advanced/": {"status_code": 301},
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
        return self.client.login(username="owner", password="test")

    def is_admin(self):
        return True


class PublicProjectUserAccessTest(PublicProjectMixin, TestCase):
    def login(self):
        return self.client.login(username="tester", password="test")

    def is_admin(self):
        return False


class PublicProjectUnauthAccessTest(PublicProjectMixin, TestCase):
    def login(self):
        pass

    def is_admin(self):
        return False


# ## Private Project Testing ###


@mock.patch("readthedocs.core.utils.trigger_build", mock.MagicMock())
class PrivateProjectAdminAccessTest(PrivateProjectMixin, TestCase):
    response_data = {
        # Places where we 302 on success, and 301 for old pages -- These delete pages should probably be 405'ing
        "/dashboard/import/manual/demo/": {"status_code": 302},
        "/dashboard/pip/": {"status_code": 301},
        "/dashboard/pip/subprojects/delete/sub/": {"status_code": 302},
        "/dashboard/pip/advanced/": {"status_code": 301},
        # 405's where we should be POST'ing
        "/dashboard/pip/users/delete/": {"status_code": 405},
        "/dashboard/pip/notifications/delete/": {"status_code": 405},
        "/dashboard/pip/redirects/{redirect_pk}/delete/": {"status_code": 405},
        "/dashboard/pip/redirects/{redirect_pk}/insert/{position}/": {
            "status_code": 405
        },
        "/dashboard/pip/subprojects/sub/delete/": {"status_code": 405},
        "/dashboard/pip/integrations/sync/": {"status_code": 405},
        "/dashboard/pip/integrations/{integration_id}/sync/": {"status_code": 405},
        "/dashboard/pip/integrations/{integration_id}/delete/": {"status_code": 405},
        "/dashboard/pip/environmentvariables/{environmentvariable_id}/delete/": {
            "status_code": 405
        },
        "/dashboard/pip/translations/delete/sub/": {"status_code": 405},
        "/dashboard/pip/version/latest/delete_html/": {"status_code": 405},
        "/dashboard/pip/rules/{automation_rule_id}/delete/": {"status_code": 405},
        "/dashboard/pip/rules/{automation_rule_id}/move/{steps}/": {"status_code": 405},
        "/dashboard/pip/webhooks/{webhook_id}/delete/": {"status_code": 405},
        # Placeholder URLs.
        "/dashboard/pip/sharing/": {"status_code": 404},
        "/dashboard/pip/keys/": {"status_code": 404},
    }

    def get_url_path_ctx(self):
        return {
            "integration_id": self.integration.id,
            "environmentvariable_id": self.environment_variable.id,
            "automation_rule_id": self.automation_rule.id,
            "webhook_id": self.webhook.id,
            "redirect_pk": self.redirect.pk,
            "steps": 1,
            "position": 0,
        }

    def login(self):
        return self.client.login(username="owner", password="test")

    def is_admin(self):
        return True


@mock.patch("readthedocs.core.utils.trigger_build", mock.MagicMock())
class PrivateProjectUserAccessTest(PrivateProjectMixin, TestCase):
    response_data = {
        # Auth'd users can import projects, have no perms on pip
        "/dashboard/": {"status_code": 200},
        "/dashboard/import/": {"status_code": 200},
        "/dashboard/import/manual/": {"status_code": 200},
        "/dashboard/import/manual/demo/": {"status_code": 302},
        "/dashboard/pip/advanced/": {"status_code": 301},
        # Unauth access redirect for non-owners
        "/dashboard/pip/": {"status_code": 301},
        # 405's where we should be POST'ing
        "/dashboard/pip/users/delete/": {"status_code": 405},
        "/dashboard/pip/notifications/delete/": {"status_code": 405},
        "/dashboard/pip/redirects/{redirect_pk}/delete/": {"status_code": 405},
        "/dashboard/pip/redirects/{redirect_pk}/insert/{position}/": {
            "status_code": 405
        },
        "/dashboard/pip/subprojects/sub/delete/": {"status_code": 405},
        "/dashboard/pip/integrations/sync/": {"status_code": 405},
        "/dashboard/pip/integrations/{integration_id}/sync/": {"status_code": 405},
        "/dashboard/pip/integrations/{integration_id}/delete/": {"status_code": 405},
        "/dashboard/pip/environmentvariables/{environmentvariable_id}/delete/": {
            "status_code": 405
        },
        "/dashboard/pip/translations/delete/sub/": {"status_code": 405},
        "/dashboard/pip/version/latest/delete_html/": {"status_code": 405},
        "/dashboard/pip/rules/{automation_rule_id}/delete/": {"status_code": 405},
        "/dashboard/pip/rules/{automation_rule_id}/move/{steps}/": {"status_code": 405},
        "/dashboard/pip/webhooks/{webhook_id}/delete/": {"status_code": 405},
    }

    # Filtered out by queryset on projects that we don't own.
    default_status_code = 404

    def get_url_path_ctx(self):
        return {
            "integration_id": self.integration.id,
            "environmentvariable_id": self.environment_variable.id,
            "automation_rule_id": self.automation_rule.id,
            "webhook_id": self.webhook.id,
            "redirect_pk": self.redirect.pk,
            "steps": 1,
            "position": 0,
        }

    def login(self):
        return self.client.login(username="tester", password="test")

    def is_admin(self):
        return False


class PrivateProjectUnauthAccessTest(PrivateProjectMixin, TestCase):
    # Auth protected
    default_status_code = 302

    response_data = {
        # Placeholder URLs.
        "/dashboard/pip/sharing/": {"status_code": 404},
        "/dashboard/pip/keys/": {"status_code": 404},
    }

    def login(self):
        pass

    def is_admin(self):
        return False


class APIMixin(URLAccessMixin):
    def setUp(self):
        super().setUp()
        self.build = get(Build, project=self.pip, version=self.pip.versions.first())
        self.build_command_result = get(BuildCommandResult, build=self.build)
        self.domain = get(Domain, domain="docs.foobar.com", project=self.pip)
        self.social_account = get(SocialAccount)
        self.remote_org = get(RemoteOrganization)
        self.remote_repo = get(RemoteRepository, organization=self.remote_org)
        self.integration = get(Integration, project=self.pip, provider_data="")
        self.default_kwargs = {
            "project_slug": self.pip.slug,
            "version_slug": self.pip.versions.all()[0].slug,
            "format": "json",
            "pk": self.pip.pk,
            "task_id": "Nope",
        }
        self.request_data = {
            "build-detail": {"pk": self.build.pk},
            "buildcommandresult-detail": {"pk": self.build_command_result.pk},
            "version-detail": {"pk": self.pip.versions.all()[0].pk},
            "domain-detail": {"pk": self.domain.pk},
            "remoteorganization-detail": {"pk": self.remote_org.pk},
            "remoterepository-detail": {"pk": self.remote_repo.pk},
            "remoteaccount-detail": {"pk": self.social_account.pk},
            "api_webhook": {"integration_pk": self.integration.pk},
            "api_webhook_stripe": {},
        }
        self.response_data = {
            "domain-list": {"status_code": 410},
            "buildcommandresult-list": {"status_code": 410},
            "build-concurrent": {"status_code": 403},
            "build-list": {"status_code": 410},
            "build-reset": {"status_code": 403},
            "project-sync-versions": {"status_code": 403},
            "project-token": {"status_code": 403},
            "emailhook-list": {"status_code": 403},
            "emailhook-detail": {"status_code": 403},
            "embed": {"status_code": 400},
            "docurl": {"status_code": 400},
            "cname": {"status_code": 400},
            "index_search": {"status_code": 403},
            "api_search": {"status_code": 400},
            "api_project_search": {"status_code": 400},
            "api_section_search": {"status_code": 400},
            "api_sync_remote_repositories": {"status_code": 403},
            "api_webhook": {"status_code": 405},
            "api_webhook_github": {"status_code": 405},
            "api_webhook_gitlab": {"status_code": 405},
            "api_webhook_bitbucket": {"status_code": 405},
            "api_webhook_generic": {"status_code": 403},
            "api_webhook_stripe": {"status_code": 405},
            "sphinxdomain-detail": {"status_code": 404},
            "project-list": {"status_code": 410},
            "remoteorganization-detail": {"status_code": 404},
            "remoterepository-detail": {"status_code": 404},
            "remoteaccount-detail": {"status_code": 404},
            "version-list": {"status_code": 410},
        }


class PublicUserProfileMixin(URLAccessMixin):
    def setUp(self):
        super().setUp()
        self.default_kwargs.update(
            {
                "username": self.tester.username,
            }
        )

    def test_public_urls(self):
        from readthedocs.profiles.urls.public import urlpatterns

        self._test_url(urlpatterns)


class PublicUserProfileAdminAccessTest(PublicUserProfileMixin, TestCase):
    def login(self):
        return self.client.login(username="owner", password="test")

    def is_admin(self):
        return True


class PublicUserProfileUserAccessTest(PublicUserProfileMixin, TestCase):
    def login(self):
        return self.client.login(username="tester", password="test")

    def is_admin(self):
        return False


class PublicUserProfileUnauthAccessTest(PublicUserProfileMixin, TestCase):
    def login(self):
        pass

    def is_admin(self):
        return False


class PrivateUserProfileMixin(URLAccessMixin):
    def setUp(self):
        super().setUp()

        self.response_data.update(
            {
                "/accounts/tokens/create/": {"status_code": 405},
                "/accounts/tokens/delete/": {"status_code": 405},
            }
        )

        self.default_kwargs.update(
            {
                "username": self.tester.username,
            }
        )

    def test_private_urls(self):
        from readthedocs.profiles.urls.private import urlpatterns

        self._test_url(urlpatterns)


class PrivateUserProfileAdminAccessTest(PrivateUserProfileMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.response_data.update(
            {
                "/accounts/login/": {"status_code": 302},
                # The test user doesn't have a GitHub account, so it's redirected to the home page.
                "/accounts/migrate-to-github-app/": {"status_code": 302},
            }
        )

    def login(self):
        return self.client.login(username="owner", password="test")

    def is_admin(self):
        return True


class PrivateUserProfileUserAccessTest(PrivateUserProfileMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.response_data.update(
            {
                "/accounts/login/": {"status_code": 302},
                # The test user doesn't have a GitHub account, so it's redirected to the home page.
                "/accounts/migrate-to-github-app/": {"status_code": 302},
            }
        )

    def login(self):
        return self.client.login(username="tester", password="test")

    def is_admin(self):
        return False


class PrivateUserProfileUnauthAccessTest(PrivateUserProfileMixin, TestCase):
    # Auth protected
    default_status_code = 302

    def setUp(self):
        super().setUp()

        self.response_data.update(
            {
                "/accounts/tokens/create/": {"status_code": 302},
                "/accounts/tokens/delete/": {"status_code": 302},
                "/accounts/login/": {"status_code": 200},
            }
        )

    def login(self):
        pass

    def is_admin(self):
        return False
