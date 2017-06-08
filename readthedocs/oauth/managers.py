"""Managers for OAuth models"""

from readthedocs.privacy.loader import RelatedUserQuerySet


class RemoteRepositoryQuerySet(RelatedUserQuerySet):
    pass


class RemoteOrganizationQuerySet(RelatedUserQuerySet):
    pass
