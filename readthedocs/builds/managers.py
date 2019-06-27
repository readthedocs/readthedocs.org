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
    EXTERNAL,
)
from .querysets import VersionQuerySet, BuildQuerySet

log = logging.getLogger(__name__)


__all__ = ['VersionManager']


class VersionManagerBaseClass(models.Manager):

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


class VersionManagerBase(VersionManagerBaseClass):

    """
    Only used for showing warning messages in test suite.

    this will override the 'get_queryset' method and add a warning message
    ehen ever 'Version.objects.*' is called in the test suite.
    """

    def get_queryset(self):
        import warnings

        warnings.warn(
            "Version.objects manager is being used"
        )
        return super().get_queryset()


class InternalVersionManagerBase(VersionManagerBaseClass):

    """
    Version manager that only includes internal version.

    It will exclude pull request/merge request versions from the queries
    and only include BRANCH, TAG, UNKONWN type Versions.
    """

    def get_queryset(self):
        return super().get_queryset().exclude(type=EXTERNAL)


class ExternalVersionManagerBase(VersionManagerBaseClass):

    """
    Version manager that only includes external version.

    It will only include pull request/merge request Versions in the queries.
    """

    def get_queryset(self):
        return super().get_queryset().filter(type=EXTERNAL)


class VersionManager(SettingsOverrideObject):
    _default_class = VersionManagerBase
    _override_setting = 'VERSION_MANAGER'


class InternalVersionManager(SettingsOverrideObject):
    _default_class = InternalVersionManagerBase


class ExternalVersionManager(SettingsOverrideObject):
    _default_class = ExternalVersionManagerBase


class BuildManagerBase(models.Manager):

    """
    Build manager for manager only queries.

    For creating different Managers.
    """

    @classmethod
    def from_queryset(cls, queryset_class, class_name=None):
        # This is overridden because :py:meth:`models.Manager.from_queryset`
        # uses `inspect` to retrieve the class methods, and the proxy class has
        # no direct members.
        queryset_class = get_override_class(
            BuildQuerySet,
            BuildQuerySet._default_class,  # pylint: disable=protected-access
        )
        return super().from_queryset(queryset_class, class_name)


class InternalBuildManagerBase(BuildManagerBase):

    """
    Build manager that only includes internal version builds.

    It will exclude pull request/merge request version builds from the queries
    and only include BRANCH, TAG, UNKONWN type Version builds.
    """

    def get_queryset(self):
        return super().get_queryset().exclude(version__type=EXTERNAL)


class ExternalBuildManagerBase(BuildManagerBase):

    """
    Build manager that only includes external version builds.

    It will only include pull request/merge request version builds in the queries.
    """

    def get_queryset(self):
        return super().get_queryset().filter(version__type=EXTERNAL)


class BuildManager(SettingsOverrideObject):
    _default_class = BuildManagerBase


class InternalBuildManager(SettingsOverrideObject):
    _default_class = InternalBuildManagerBase


class ExternalBuildManager(SettingsOverrideObject):
    _default_class = ExternalBuildManagerBase
