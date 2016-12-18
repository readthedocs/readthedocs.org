"""Managers for OAuth models"""

from readthedocs.privacy.loader import RelatedUserManager


class RemoteRepositoryManager(RelatedUserManager):
    pass


class RemoteOrganizationManager(RelatedUserManager):
    pass
