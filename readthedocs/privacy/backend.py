
from django.db import models

from guardian.shortcuts import get_objects_for_user

from projects import constants


class ProjectManager(models.Manager):

    def _add_user_repos(self, queryset, user):
        # Avoid circular import
        from projects.models import Project
        # Show all projects to super user
        if user.has_perm('projects.view_project'):
            return Project.objects.all()
        # Show user projects to user
        if user.is_authenticated():
            # Add in possible user-specific views
            user_queryset = get_objects_for_user(user, 'projects.view_project')
            return user_queryset | queryset
        # User has no special privs
        return queryset

    def for_user_and_viewer(self, user, viewer, *args, **kwargs):
        """
        Show projects that a user owns, that another user can see.
        """
        queryset = self.filter(privacy_level=constants.PUBLIC)
        queryset = self._add_user_repos(queryset, viewer)
        queryset = queryset.filter(users__in=[user])
        return queryset

    def for_admin_user(self, user=None, *args, **kwargs):
        return self.filter(users__in=[user])

    def dashboard(self, user=None, *args, **kwargs):
        return self.for_admin_user(user)

    def public(self, user=None, *args, **kwargs):
        queryset = self.filter(privacy_level=constants.PUBLIC)
        if user:
            return self._add_user_repos(queryset, user)
        else:
            return queryset


class RelatedProjectManager(models.Manager):

    def _add_user_repos(self, queryset, user=None, *args, **kwargs):
        # Hack around get_objects_for_user not supporting global perms
        if user.has_perm('projects.view_project'):
            return self.get_queryset().all()
        if user.is_authenticated():
            # Add in possible user-specific views
            project_qs = get_objects_for_user(user, 'projects.view_project')
            pks = [p.pk for p in project_qs]
            queryset = self.get_queryset().filter(project__pk__in=pks) | queryset
        return queryset

    def public(self, user=None, project=None, *args, **kwargs):
        queryset = self.filter(project__privacy_level=constants.PUBLIC)
        if user:
            queryset = self._add_user_repos(queryset, user)
        if project:
            queryset = queryset.filter(project=project)
        return queryset


class VersionManager(RelatedProjectManager):

    def public(self, user=None, project=None, only_active=True, *args, **kwargs):
        queryset = super(VersionManager, self).public(user, project)
        if only_active:
            queryset = queryset.filter(active=True)
        return queryset

    def _add_user_repos(self, queryset, user=None, *args, **kwargs):
        super(VersionManager, self)._add_user_repos(queryset, user)
        if user and user.is_authenticated():
            # Add in possible user-specific views
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            queryset = user_queryset | queryset
        elif user:
            # Hack around get_objects_for_user not supporting global perms
            global_access = user.has_perm('builds.view_version')
            if global_access:
                queryset = self.get_queryset().all()
        return queryset


class AdminPermission(object):

    @classmethod
    def is_admin(cls, user, project):
        return user in project.users.all()
