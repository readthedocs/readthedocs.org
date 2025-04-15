"""Managers for OAuth models."""

from django.db import models

from readthedocs.core.querysets import NoReprQuerySet
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.constants import GITHUB_APP


class RelatedUserQuerySet(NoReprQuerySet, models.QuerySet):
    """For models with relations through :py:class:`User`."""

    def api(self, user=None):
        """Return objects for user."""
        if not user.is_authenticated:
            return self.none()
        queryset = self.filter(users=user)

        # If the user has already started using the GitHub App,
        # we shouldn't show repositories from the old GitHub integration.
        if queryset.filter(vcs_provider=GITHUB_APP).exists():
            queryset = queryset.exclude(vcs_provider=GITHUB)

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

        # If the user has already started using the GitHub App,
        # we shouldn't show repositories from the old GitHub integration.
        if queryset.filter(vcs_provider=GITHUB_APP).exists():
            queryset = queryset.exclude(vcs_provider=GITHUB)

        return queryset.distinct()


class RemoteOrganizationQuerySet(RelatedUserQuerySet):
    pass
