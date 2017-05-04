"""Managers for OAuth models"""
from __future__ import absolute_import, division, print_function

from readthedocs.privacy.loader import RelatedUserManager


class RemoteRepositoryManager(RelatedUserManager):
    pass


class RemoteOrganizationManager(RelatedUserManager):
    pass
