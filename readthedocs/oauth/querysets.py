"""Managers for OAuth models."""

from django.db import models
from django.db.models import Q

from readthedocs.core.querysets import NoReprQuerySet


class RelatedUserQuerySet(NoReprQuerySet, models.QuerySet):
    """For models with relations through :py:class:`User`."""

    def api(self, user=None):
        """Return objects for user."""
        if not user.is_authenticated:
            return self.none()
        return self.filter(users=user)

    def api_v2(self, *args, **kwargs):
        # API v2 is the same as API v3 for .org, but it's
        # different for .com, this method is overridden there.
        return self.api(*args, **kwargs)


class RemoteRepositoryQuerySet(RelatedUserQuerySet):
    def for_project_linking(self, user):
        """
        Return repositories that can be linked to a project by the given user.

        Repositories can be imported if:

        - The user has read or adming access to the repository on the VCS service.
        - If the repository is private, the user must be an admin.
        - If the repository is public, the user doesn't need to be an admin.
        """
        query = Q(remote_repository_relations__user=user) & (
            Q(private=False) | Q(private=True, remote_repository_relations__admin=True)
        )
        return self.filter(query).distinct()


class RemoteOrganizationQuerySet(RelatedUserQuerySet):
    pass
