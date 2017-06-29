"""Managers for OAuth models"""

from __future__ import absolute_import

from django.db import models

from readthedocs.core.utils.extend import SettingsOverrideObject


class RelatedUserQuerySetBase(models.QuerySet):

    """For models with relations through :py:class:`User`"""

    def api(self, user=None):
        """Return objects for user"""
        if not user.is_authenticated():
            return self.none()
        return self.filter(users=user)


class RelatedUserQuerySet(SettingsOverrideObject):
    _default_class = RelatedUserQuerySetBase
    _override_setting = 'RELATED_USER_MANAGER'


class RemoteRepositoryQuerySet(RelatedUserQuerySet):
    pass


class RemoteOrganizationQuerySet(RelatedUserQuerySet):
    pass
