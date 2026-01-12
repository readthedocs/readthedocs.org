"""OAuth utility functions."""

import re
from functools import cached_property
from typing import Iterator

import structlog
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError
from requests.exceptions import RequestException

from readthedocs.core.permissions import AdminPermission
from readthedocs.oauth.clients import get_oauth2_client
from readthedocs.oauth.models import RemoteRepository


log = structlog.get_logger(__name__)


class SyncServiceError(Exception):
    """Error raised when a service failed to sync."""

    INVALID_OR_REVOKED_ACCESS_TOKEN = _(
        "Our access to your following accounts was revoked: {provider}. "
        "Please, reconnect them from your social account connections."
    )


class Service:
    """Base class for service that interacts with a VCS provider and a project."""

    vcs_provider_slug: str
    allauth_provider = type[OAuth2Provider]

    url_pattern: re.Pattern | None = None
    default_user_avatar_url = settings.OAUTH_AVATAR_USER_DEFAULT_URL
    default_org_avatar_url = settings.OAUTH_AVATAR_ORG_DEFAULT_URL
    supports_build_status = False
    supports_clone_token = False
    supports_commenting = False

    @classmethod
    def for_project(cls, project):
        """Return an iterator of services that can be used for the project."""
        raise NotImplementedError

    @classmethod
    def for_user(cls, user):
        """Return an iterator of services that belong to the user."""
        raise NotImplementedError

    @classmethod
    def sync_user_access(cls, user):
        """Sync the user's access to the provider's repositories and organizations."""
        raise NotImplementedError

    def sync(self):
        """
        Sync remote repositories and organizations.

        - Creates a new RemoteRepository/Organization per new repository
        - Updates fields for existing RemoteRepository/Organization
        - Deletes old RemoteRepository/Organization that are no longer present
          in this provider.
        """
        raise NotImplementedError

    def update_repository(self, remote_repository: RemoteRepository):
        """
        Update a repository using the service API.

        This also updates the user relationship with the repository,
        if user is an admin or not, and in case the user no longer has access
        to the repository, the relationship is removed.
        In the case of services that aren't linked to a user (GitHub Apps),
        this method will update the permissions of all users that have access
        to the repository.
        """
        raise NotImplementedError

    def setup_webhook(self, project, integration=None) -> bool:
        """
        Setup webhook for project.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: boolean based on webhook set up success
        """
        raise NotImplementedError

    def update_webhook(self, project, integration) -> bool:
        """
        Update webhook integration.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Webhook integration to update
        :type integration: Integration
        :returns: boolean based on webhook update success, and requests Response object
        """
        raise NotImplementedError

    def send_build_status(self, *, build, commit, status):
        """
        Create commit status for project.

        :param build: Build to set up commit status for
        :type build: Build
        :param commit: commit sha of the pull/merge request
        :type commit: str
        :param status: build state failure, pending, or success.
        :type status: str
        :returns: boolean based on commit status creation was successful or not.
        :rtype: Bool
        """
        raise NotImplementedError

    def get_clone_token(self, project):
        """Get a token used for cloning the repository."""
        raise NotImplementedError

    def post_comment(self, build, comment: str, create_new: bool = True):
        """
        Post a comment on the pull request attached to the build.

        :param create_new: Create a new comment if one doesn't exist.
        """
        raise NotImplementedError

    @classmethod
    def is_project_service(cls, project):
        """
        Determine if this is the service the project is using.

        .. note::

            This should be deprecated in favor of attaching the
            :py:class:`RemoteRepository` to the project instance. This is a
            slight improvement on the legacy check for webhooks
        """
        return cls.url_pattern is not None and cls.url_pattern.search(project.repo) is not None


class UserService(Service):
    """
    Subclass of Service that interacts with a VCS provider using the user's OAuth token.

    :param user: User to use in token lookup and session creation
    :param account: :py:class:`SocialAccount` instance for user
    """

    def __init__(self, user, account):
        self.user = user
        self.account = account
        # Cache organizations to avoid multiple DB hits
        # when syncing repositories that belong to the same organization.
        # Used by `create_organization` method in subclasses.
        self._organizations_cache = {}
        structlog.contextvars.bind_contextvars(
            user_username=self.user.username,
            social_provider=self.allauth_provider.id,
            social_account_id=self.account.pk,
        )

    @classmethod
    def for_project(cls, project):
        users = AdminPermission.admins(project)
        for user in users:
            yield from cls.for_user(user)

    @classmethod
    def for_user(cls, user):
        accounts = SocialAccount.objects.filter(
            user=user,
            provider=cls.allauth_provider.id,
        )
        for account in accounts:
            yield cls(user=user, account=account)

    @classmethod
    def sync_user_access(cls, user):
        """
        Sync the user's access to the provider repositories and organizations.

        Since UserService makes use of the user's OAuth token,
        we can just sync the user's repositories in order to
        update the user access to repositories and organizations.

        :raises SyncServiceError: if the access token is invalid or revoked
        """
        has_error = False
        for service in cls.for_user(user):
            try:
                service.sync()
            except SyncServiceError:
                # Don't stop the sync if one service account fails,
                # as we should try to sync all accounts.
                has_error = True
        if has_error:
            raise SyncServiceError()

    @cached_property
    def session(self):
        return get_oauth2_client(self.account)

    def paginate(self, url, **kwargs) -> Iterator[dict]:
        """
        Recursively combine results from service's pagination.

        :param url: start url to get the data from.
        :type url: unicode
        :param kwargs: optional parameters passed to .get() method
        :type kwargs: dict
        """
        resp = None
        try:
            resp = self.session.get(url, params=kwargs)

            # TODO: this check of the status_code would be better in the
            # ``create_session`` method since it could be used from outside, but
            # I didn't find a generic way to make a test request to each
            # provider.
            if resp.status_code in [401, 403]:
                # Bad credentials: the token we have in our database is not
                # valid. Probably the user has revoked the access to our App. He
                # needs to reconnect his account
                raise SyncServiceError(
                    SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                        provider=self.allauth_provider.name
                    )
                )

            next_url = self.get_next_url_to_paginate(resp)
            yield from self.get_paginated_results(resp)
            if next_url:
                yield from self.paginate(next_url)
        # Catch specific exception related to OAuth
        except InvalidClientIdError:
            log.warning("access_token or refresh_token failed.", url=url)
            raise SyncServiceError(
                SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                    provider=self.allauth_provider.name
                )
            )
        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            # Response data should always be JSON, still try to log if not
            # though
            try:
                debug_data = resp.json() if resp else {}
            except ValueError:
                debug_data = resp.content
            log.debug(
                "Paginate failed at URL.",
                url=url,
                debug_data=debug_data,
            )

        return []

    def sync(self):
        """
        Sync repositories (RemoteRepository) and organizations (RemoteOrganization).

        - creates a new RemoteRepository/Organization per new repository
        - updates fields for existing RemoteRepository/Organization
        - deletes old RemoteRepository/Organization that are not present
          for this user in the current provider
        """
        repository_remote_ids = self.sync_repositories()
        (
            organization_remote_ids,
            organization_repositories_remote_ids,
        ) = self.sync_organizations()

        # Delete RemoteRepository where the user doesn't have access anymore
        # (skip RemoteRepository tied to a Project on this user)
        repository_remote_ids += organization_repositories_remote_ids
        (
            self.user.remote_repository_relations.filter(
                account=self.account,
                remote_repository__vcs_provider=self.vcs_provider_slug,
            )
            .exclude(
                remote_repository__remote_id__in=repository_remote_ids,
            )
            .delete()
        )

        # Delete RemoteOrganization where the user doesn't have access anymore
        (
            self.user.remote_organization_relations.filter(
                account=self.account,
                remote_organization__vcs_provider=self.vcs_provider_slug,
            )
            .exclude(
                remote_organization__remote_id__in=organization_remote_ids,
            )
            .delete()
        )

    def get_next_url_to_paginate(self, response):
        """
        Return the next url to feed the `paginate` method.

        :param response: response from where to get the `next_url` attribute
        :type response: requests.Response
        """
        raise NotImplementedError

    def get_paginated_results(self, response):
        """
        Return the results for the current response/page.

        :param response: response from where to get the results.
        :type response: requests.Response
        """
        raise NotImplementedError

    def get_webhook_url(self, project, integration):
        """Get the webhook URL for the project's integration."""
        return "{base_url}{path}".format(
            base_url=settings.PUBLIC_API_URL,
            path=reverse(
                "api_webhook",
                kwargs={
                    "project_slug": project.slug,
                    "integration_pk": integration.pk,
                },
            ),
        )

    def get_provider_data(self, project, integration):
        """
        Gets provider data from Git Providers Webhooks API.

        :param project: project
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: Dictionary containing provider data from the API or None
        :rtype: dict
        """
        raise NotImplementedError

    def sync_repositories(self):
        raise NotImplementedError

    def sync_organizations(self):
        raise NotImplementedError
