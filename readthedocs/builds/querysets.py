"""Build and Version QuerySet classes"""

from __future__ import absolute_import

from django.db import models
from guardian.shortcuts import get_objects_for_user

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects import constants


__all__ = ['VersionQuerySet', 'BuildQuerySet', 'RelatedBuildQuerySet']


class VersionQuerySetBase(models.QuerySet):

    """Versions take into account their own privacy_level setting."""

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user):
        if user.has_perm('builds.view_version'):
            return self.all().distinct()
        if user.is_authenticated():
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            queryset = user_queryset | queryset
        return queryset.distinct()

    def public(self, user=None, project=None, only_active=True):
        queryset = self.filter(privacy_level=constants.PUBLIC)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        if only_active:
            queryset = queryset.filter(active=True)
        return queryset

    def protected(self, user=None, project=None, only_active=True):
        queryset = self.filter(privacy_level__in=[constants.PUBLIC, constants.PROTECTED])
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        if only_active:
            queryset = queryset.filter(active=True)
        return queryset

    def private(self, user=None, project=None, only_active=True):
        queryset = self.filter(privacy_level__in=[constants.PRIVATE])
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        if only_active:
            queryset = queryset.filter(active=True)
        return queryset

    def api(self, user=None):
        return self.public(user, only_active=False)

    def for_project(self, project):
        """Return all versions for a project, including translations"""
        return self.filter(
            models.Q(project=project) |
            models.Q(project__main_language_project=project)
        )


class VersionQuerySet(SettingsOverrideObject):
    _default_class = VersionQuerySetBase


class BuildQuerySetBase(models.QuerySet):

    """
    Build objects that are privacy aware.

    i.e. they take into account the privacy of the Version that they relate to.
    """

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user=None):
        if user.has_perm('builds.view_version'):
            return self.all().distinct()
        if user.is_authenticated():
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            pks = [p.pk for p in user_queryset]
            queryset = self.filter(version__pk__in=pks) | queryset
        return queryset.distinct()

    def public(self, user=None, project=None):
        queryset = self.filter(version__privacy_level=constants.PUBLIC)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset

    def api(self, user=None):
        return self.public(user)


class BuildQuerySet(SettingsOverrideObject):
    _default_class = BuildQuerySetBase
    _override_setting = 'BUILD_MANAGER'


class RelatedBuildQuerySetBase(models.QuerySet):

    """For models with association to a project through :py:class:`Build`"""

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user=None):
        if user.has_perm('builds.view_version'):
            return self.all().distinct()
        if user.is_authenticated():
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            pks = [p.pk for p in user_queryset]
            queryset = self.filter(
                build__version__pk__in=pks) | queryset
        return queryset.distinct()

    def public(self, user=None, project=None):
        queryset = self.filter(build__version__privacy_level=constants.PUBLIC)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(build__project=project)
        return queryset

    def api(self, user=None):
        return self.public(user)


class RelatedBuildQuerySet(SettingsOverrideObject):
    _default_class = RelatedBuildQuerySetBase
    _override_setting = 'RELATED_BUILD_MANAGER'
