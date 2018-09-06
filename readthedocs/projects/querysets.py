"""Project model QuerySet classes"""

from __future__ import absolute_import

from django.db import models
from django.db.models import Q
from guardian.shortcuts import get_objects_for_user

from . import constants
from readthedocs.core.utils.extend import SettingsOverrideObject


class ProjectQuerySetBase(models.QuerySet):

    """Projects take into account their own privacy_level setting."""

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user):
        if user.has_perm('projects.view_project'):
            return self.all().distinct()
        if user.is_authenticated():
            user_queryset = get_objects_for_user(user, 'projects.view_project')
            queryset = user_queryset | queryset
        return queryset.distinct()

    def for_user_and_viewer(self, user, viewer):
        """Show projects that a user owns, that another user can see."""
        queryset = self.filter(privacy_level=constants.PUBLIC)
        queryset = self._add_user_repos(queryset, viewer)
        queryset = queryset.filter(users__in=[user])
        return queryset

    def for_admin_user(self, user):
        if user.is_authenticated():
            return self.filter(users__in=[user])
        return self.none()

    def public(self, user=None):
        queryset = self.filter(privacy_level=constants.PUBLIC)
        if user:
            return self._add_user_repos(queryset, user)
        return queryset

    def protected(self, user=None):
        queryset = self.filter(privacy_level__in=[constants.PUBLIC, constants.PROTECTED])
        if user:
            return self._add_user_repos(queryset, user)
        return queryset

    def private(self, user=None):
        queryset = self.filter(privacy_level=constants.PRIVATE)
        if user:
            return self._add_user_repos(queryset, user)
        return queryset

    # Aliases

    def dashboard(self, user=None):
        return self.for_admin_user(user)

    def api(self, user=None):
        return self.public(user)


class ProjectQuerySet(SettingsOverrideObject):
    _default_class = ProjectQuerySetBase
    _override_setting = 'PROJECT_MANAGER'


class RelatedProjectQuerySetBase(models.QuerySet):

    """
    A manager for things that relate to Project and need to get their perms from the project.

    This shouldn't be used as a subclass.
    """

    use_for_related_fields = True
    project_field = 'project'

    def _add_user_repos(self, queryset, user=None):
        # Hack around get_objects_for_user not supporting global perms
        if user.has_perm('projects.view_project'):
            return self.all().distinct()
        if user.is_authenticated():
            # Add in possible user-specific views
            project_qs = get_objects_for_user(user, 'projects.view_project')
            pks = project_qs.values_list('pk', flat=True)
            kwargs = {'%s__pk__in' % self.project_field: pks}
            queryset = self.filter(**kwargs) | queryset
        return queryset.distinct()

    def public(self, user=None, project=None):
        kwargs = {'%s__privacy_level' % self.project_field: constants.PUBLIC}
        queryset = self.filter(**kwargs)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset

    def protected(self, user=None, project=None):
        kwargs = {
            '%s__privacy_level__in' % self.project_field: [constants.PUBLIC, constants.PROTECTED]
        }
        queryset = self.filter(**kwargs)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset

    def private(self, user=None, project=None):
        kwargs = {
            '%s__privacy_level' % self.project_field: constants.PRIVATE,
        }
        queryset = self.filter(**kwargs)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset

    def api(self, user=None):
        return self.public(user)


class RelatedProjectQuerySet(SettingsOverrideObject):
    _default_class = RelatedProjectQuerySetBase
    _override_setting = 'RELATED_PROJECT_MANAGER'


class ParentRelatedProjectQuerySetBase(RelatedProjectQuerySetBase):
    project_field = 'parent'
    use_for_related_fields = True


class ParentRelatedProjectQuerySet(SettingsOverrideObject):
    _default_class = ParentRelatedProjectQuerySetBase
    _override_setting = 'RELATED_PROJECT_MANAGER'


class ChildRelatedProjectQuerySetBase(RelatedProjectQuerySetBase):
    project_field = 'child'
    use_for_related_fields = True


class ChildRelatedProjectQuerySet(SettingsOverrideObject):
    _default_class = ChildRelatedProjectQuerySetBase
    _override_setting = 'RELATED_PROJECT_MANAGER'


class FeatureQuerySet(models.QuerySet):
    use_for_related_fields = True

    def for_project(self, project):
        return self.filter(
            Q(projects=project) |
            Q(default_true=True, add_date__gt=project.pub_date)
        ).distinct()
