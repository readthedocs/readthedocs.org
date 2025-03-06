"""Build and Version class model Managers."""

import structlog
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import LATEST
from readthedocs.builds.constants import LATEST_VERBOSE_NAME
from readthedocs.builds.constants import STABLE
from readthedocs.builds.constants import STABLE_VERBOSE_NAME
from readthedocs.builds.constants import TAG
from readthedocs.builds.querysets import VersionQuerySet
from readthedocs.core.utils.extend import get_override_class


log = structlog.get_logger(__name__)


__all__ = ["VersionManager"]


class VersionManager(models.Manager):
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
            VersionQuerySet._default_class,
        )
        return super().from_queryset(queryset_class, class_name)

    def create_stable(self, **kwargs):
        defaults = {
            "slug": STABLE,
            "verbose_name": STABLE_VERBOSE_NAME,
            "machine": True,
            "active": True,
            # TODO: double-check if we still require the `identifier: STABLE` field.
            # At the time of creation, we don't really know what's the branch/tag identifier
            # for the STABLE version. It makes sense to be `None`, probably.
            #
            # Note that we removed the `identifier: LATEST` from `create_latest` as a way to
            # use the default branch.
            "identifier": STABLE,
            "type": TAG,
        }
        defaults.update(kwargs)
        return self.create(**defaults)

    def create_latest(self, **kwargs):
        defaults = {
            "slug": LATEST,
            "verbose_name": LATEST_VERBOSE_NAME,
            "machine": True,
            "active": True,
            "type": BRANCH,
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
            log.warning("Version not found for given kwargs.", kwargs=kwargs)


class InternalVersionManager(VersionManager):
    """
    Version manager that only includes internal version.

    It will exclude pull request/merge request versions from the queries
    and only include BRANCH, TAG, UNKNOWN type Versions.
    """

    def get_queryset(self):
        return super().get_queryset().exclude(type=EXTERNAL)


class ExternalVersionManager(VersionManager):
    """
    Version manager that only includes external version.

    It will only include pull request/merge request Versions in the queries.
    """

    def get_queryset(self):
        return super().get_queryset().filter(type=EXTERNAL)


class InternalBuildManager(models.Manager):
    """
    Build manager that only includes internal version builds.

    It will exclude pull request/merge request version builds from the queries
    and only include BRANCH, TAG, UNKNOWN type Version builds.
    """

    def get_queryset(self):
        return super().get_queryset().exclude(version__type=EXTERNAL)


class ExternalBuildManager(models.Manager):
    """
    Build manager that only includes external version builds.

    It will only include pull request/merge request version builds in the queries.
    """

    def get_queryset(self):
        return super().get_queryset().filter(version__type=EXTERNAL)


class AutomationRuleMatchManager(models.Manager):
    def register_match(self, rule, version, max_registers=15):
        created = self.create(
            rule=rule,
            match_arg=rule.get_match_arg(),
            action=rule.action,
            version_name=version.verbose_name,
            version_type=version.type,
        )

        for match in self.filter(rule__project=rule.project)[max_registers:]:
            match.delete()
        return created
