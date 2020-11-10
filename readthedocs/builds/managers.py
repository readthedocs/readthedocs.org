"""Build and Version class model Managers."""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from polymorphic.managers import PolymorphicManager

from readthedocs.core.utils.extend import (
    SettingsOverrideObject,
    get_override_class,
)

from .constants import (
    BRANCH,
    EXTERNAL,
    LATEST,
    LATEST_VERBOSE_NAME,
    STABLE,
    STABLE_VERBOSE_NAME,
    TAG,
)
from .querysets import BuildQuerySet, VersionQuerySet


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
            log.warning('Version not found for given kwargs. %s', kwargs)


class InternalVersionManagerBase(VersionManagerBase):

    """
    Version manager that only includes internal version.

    It will exclude pull request/merge request versions from the queries
    and only include BRANCH, TAG, UNKNOWN type Versions.
    """

    def get_queryset(self):
        return super().get_queryset().exclude(type=EXTERNAL)


class ExternalVersionManagerBase(VersionManagerBase):

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
    and only include BRANCH, TAG, UNKNOWN type Version builds.
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


class VersionAutomationRuleManager(PolymorphicManager):

    """
    Mananger for VersionAutomationRule.

    .. note::

       This manager needs to inherit from PolymorphicManager,
       since the model is a PolymorphicModel.
       See https://django-polymorphic.readthedocs.io/page/managers.html
    """

    def add_rule(
        self, *, project, description, match_arg, version_type, action, **kwargs,
    ):
        """
        Append an automation rule to `project`.

        The rule is created with a priority lower than the last rule
        in `project`.
        """
        last_priority = (
            project.automation_rules
            .values_list('priority', flat=True)
            .order_by('priority')
            .last()
        )
        if last_priority is None:
            priority = 0
        else:
            priority = last_priority + 1

        rule = self.create(
            project=project,
            priority=priority,
            description=description,
            match_arg=match_arg,
            version_type=version_type,
            action=action,
            **kwargs,
        )
        return rule
