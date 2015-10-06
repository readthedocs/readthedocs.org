
from django.db import models

from guardian.shortcuts import get_objects_for_user

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import TAG
from readthedocs.builds.constants import LATEST
from readthedocs.builds.constants import LATEST_VERBOSE_NAME
from readthedocs.builds.constants import STABLE
from readthedocs.builds.constants import STABLE_VERBOSE_NAME
from readthedocs.projects import constants


class ProjectManager(models.Manager):

    def _add_user_repos(self, queryset, user):
        # Avoid circular import
        from readthedocs.projects.models import Project
        # Show all projects to super user
        if user.has_perm('projects.view_project'):
            return Project.objects.all().distinct()
        # Show user projects to user
        if user.is_authenticated():
            # Add in possible user-specific views
            user_queryset = get_objects_for_user(user, 'projects.view_project')
            return user_queryset | queryset
        # User has no special privs
        return queryset.distinct()

    def for_user_and_viewer(self, user, viewer, *args, **kwargs):
        """
        Show projects that a user owns, that another user can see.
        """
        queryset = self.filter(privacy_level=constants.PUBLIC)
        queryset = self._add_user_repos(queryset, viewer)
        queryset = queryset.filter(users__in=[user])
        return queryset

    def for_admin_user(self, user=None, *args, **kwargs):
        if user.is_authenticated():
            return self.filter(users__in=[user])
        else:
            return self.none()

    def public(self, user=None):
        queryset = self.filter(privacy_level=constants.PUBLIC)
        if user:
            return self._add_user_repos(queryset, user)
        else:
            return queryset

    def protected(self, user=None, *args, **kwargs):
        queryset = self.filter(privacy_level__in=[constants.PUBLIC, constants.PROTECTED])
        if user:
            return self._add_user_repos(queryset, user)
        else:
            return queryset

    # Aliases

    def dashboard(self, user=None, *args, **kwargs):
        return self.for_admin_user(user)

    def api(self, user=None):
        return self.public(user)


class RelatedProjectManager(models.Manager):

    def _add_user_repos(self, queryset, user=None):
        # Hack around get_objects_for_user not supporting global perms
        if user.has_perm('projects.view_project'):
            return self.get_queryset().all().distinct()
        if user.is_authenticated():
            # Add in possible user-specific views
            project_qs = get_objects_for_user(user, 'projects.view_project')
            pks = [p.pk for p in project_qs]
            queryset = self.get_queryset().filter(project__pk__in=pks) | queryset
        return queryset.distinct()

    def public(self, user=None, project=None):
        queryset = self.filter(project__privacy_level=constants.PUBLIC)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset

    def api(self, user=None):
        return self.public(user)


class RelatedBuildManager(models.Manager):
    '''For models with association to a project through :py:cls:`Build`'''

    def _add_user_repos(self, queryset, user=None):
        # Hack around get_objects_for_user not supporting global perms
        if user.has_perm('projects.view_project'):
            return self.get_queryset().all().distinct()
        if user.is_authenticated():
            # Add in possible user-specific views
            project_qs = get_objects_for_user(user, 'projects.view_project')
            pks = [p.pk for p in project_qs]
            queryset = (self.get_queryset()
                        .filter(build__project__pk__in=pks) | queryset)
        return queryset.distinct()

    def public(self, user=None, project=None):
        queryset = self.filter(build__project__privacy_level=constants.PUBLIC)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(build__project=project)
        return queryset

    def api(self, user=None):
        return self.public(user)


class VersionManager(RelatedProjectManager):

    def _add_user_repos(self, queryset, user=None):
        queryset = super(VersionManager, self)._add_user_repos(queryset, user)
        if user and user.is_authenticated():
            # Add in possible user-specific views
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            queryset = user_queryset.distinct() | queryset
        elif user:
            # Hack around get_objects_for_user not supporting global perms
            global_access = user.has_perm('builds.view_version')
            if global_access:
                queryset = self.get_queryset().all().distinct()
        return queryset.distinct()

    def public(self, user=None, project=None, only_active=True):
        queryset = self.filter(project__privacy_level=constants.PUBLIC,
                               privacy_level=constants.PUBLIC)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        if only_active:
            queryset = queryset.filter(active=True)
        return queryset

    def api(self, user=None):
        return self.public(user, only_active=False)

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


class AdminPermission(object):

    @classmethod
    def is_admin(cls, user, project):
        return user in project.users.all()


class AdminNotAuthorized(ValueError):
    pass


class RelatedUserManager(models.Manager):

    """For models with relations through :py:cls:`User`"""

    def api(self, user=None, *args, **kwargs):
        """Return objects for user"""
        if not user.is_authenticated():
            return self.none()
        return self.filter(users=user)
