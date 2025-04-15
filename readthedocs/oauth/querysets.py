"""Managers for OAuth models."""

from django.db import models

from readthedocs.core.querysets import NoReprQuerySet
from readthedocs.oauth.constants import GITHUB_APP


class RelatedUserQuerySet(NoReprQuerySet, models.QuerySet):
    """For models with relations through :py:class:`User`."""

    def api(self, user=None):
        """Return objects for user."""
        if not user.is_authenticated:
            return self.none()
        queryset = self.filter(users=user)
        # TODO: Once we are migrated into GitHub App we should include these repositories/organizations.
        # Exclude repositories/organizations from the GitHub App for now to avoid duplicated entries.
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
        # TODO: Once we are migrated into GitHub App we should include these repositories/organizations.
        # Exclude repositories/organizations from the GitHub App for now to avoid duplicated entries.
        queryset = queryset.exclude(vcs_provider=GITHUB_APP)
        return queryset.distinct()


class RemoteOrganizationQuerySet(RelatedUserQuerySet):
    pass
