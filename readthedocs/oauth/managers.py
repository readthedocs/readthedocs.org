"""Managers for OAuth models"""

from __future__ import absolute_import
from readthedocs.privacy.loader import RelatedUserQuerySet


class RemoteRepositoryQuerySet(RelatedUserQuerySet):
    pass


class RemoteOrganizationQuerySet(RelatedUserQuerySet):
    pass
