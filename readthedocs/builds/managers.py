# -*- coding: utf-8 -*-

"""Build and Version class model Managers."""

import logging

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from readthedocs.core.utils.extend import (
    SettingsOverrideObject,
    get_override_class,
)

from .constants import (
    BRANCH,
    LATEST,
    LATEST_VERBOSE_NAME,
    STABLE,
    STABLE_VERBOSE_NAME,
    TAG,
)
from .querysets import VersionQuerySet

log = logging.getLogger(__name__)


__all__ = ['VersionManager']


class VersionManagerBase(models.Manager):

    """
    Version manager for manager only queries.

    For queries not suitable for the :py:class:`VersionQuerySet`, such as create
    queries.
    """

    @classmethod
    def from_queryset(cls, queryset_class, class_name=None):
        # This is overridden because :py:meth:`models.Manager.from_queryset`
        # uses `inspect` to retrieve the class methods, and the proxy class has
        # no direct members.
        queryset_class = get_override_class(
            VersionQuerySet,
            VersionQuerySet._default_class,  # pylint: disable=protected-access
        )
        return super().from_queryset(queryset_class, class_name)

    def create_stable(self, **kwargs):
        defaults = {
            'slug': STABLE,
            'verbose_name': STABLE_VERBOSE_NAME,
            'machine': True,
            'active': True,
            'identifier': STABLE,
            'type': TAG,
        }
        defaults.update(kwargs)
        return self.create(**defaults)

    def create_latest(self, **kwargs):
        defaults = {
            'slug': LATEST,
            'verbose_name': LATEST_VERBOSE_NAME,
            'machine': True,
            'active': True,
            'identifier': LATEST,
            'type': BRANCH,
        }
        defaults.update(kwargs)
        return self.create(**defaults)

    def get_object_or_log(self, **kwargs):
        """
        Returns Version object or log.

        It will return the Version object if found for the given kwargs,
        otherwise it will log a warning along with all provided kwargs.
        """
        try:
            return super().get(**kwargs)
        except ObjectDoesNotExist:
            log.warning('Version not found for given kwargs. %s' % kwargs)


class VersionManager(SettingsOverrideObject):
    _default_class = VersionManagerBase
    _override_setting = 'VERSION_MANAGER'
