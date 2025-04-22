"""Managers for OAuth models."""

from django.db import models

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.core.querysets import NoReprQuerySet
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.constants import GITHUB_APP


def _has_account_connected_to_github_app(user):
    if not user:
        return False
    return user.socialaccount_set.filter(
        provider=GitHubAppProvider.id,
    ).exists()


class RelatedUserQuerySet(NoReprQuerySet, models.QuerySet):
    """For models with relations through :py:class:`User`."""

    def api(self, user=None):
        """Return objects for user."""
        if not user.is_authenticated:
            return self.none()
        queryset = self.filter(users=user)

        # Exclude repositories/organizations from the old or new GitHub App to avoid duplicated entries.
        # If the user has already started using the GitHub App,
        # we shouldn't show repositories from the old GitHub integration.
        # Otherwise, we should show the repositories from the old GitHub integration only,
        # this is done to avoid confusion for users that haven't migrated their accounts yet,
        # but still have access to some repositories from the new GitHub App integration.
        using_github_app = _has_account_connected_to_github_app(user)
        if using_github_app and queryset.filter(vcs_provider=GITHUB_APP).exists():
            queryset = queryset.exclude(vcs_provider=GITHUB)
        else:
            queryset = queryset.exclude(vcs_provider=GITHUB_APP)

        return queryset

    def api_v2(self, *args, **kwargs):
        # API v2 is the same as API v3 for .org, but it's
        # different for .com, this method is overridden there.
        return self.api(*args, **kwargs)


class RemoteRepositoryQuerySet(RelatedUserQuerySet):
    def for_project_linking(self, user):
        """
        Return repositories that can be linked to a project by the given user.

        Repositories can be linked to a project only if the user has admin access
        to the repository on the VCS service.
        """
        queryset = self.filter(
            remote_repository_relations__user=user,
            remote_repository_relations__admin=True,
        )

        # Exclude repositories/organizations from the old or new GitHub App to avoid duplicated entries.
        # If the user has already started using the GitHub App,
        # we shouldn't show repositories from the old GitHub integration.
        # Otherwise, we should show the repositories from the old GitHub integration only,
        # this is done to avoid confusion for users that haven't migrated their accounts yet,
        # but still have access to some repositories from the new GitHub App integration.
        using_github_app = _has_account_connected_to_github_app(user)
        if using_github_app and queryset.filter(vcs_provider=GITHUB_APP).exists():
            queryset = queryset.exclude(vcs_provider=GITHUB)
        else:
            queryset = queryset.exclude(vcs_provider=GITHUB_APP)

        return queryset.distinct()


class RemoteOrganizationQuerySet(RelatedUserQuerySet):
    pass
