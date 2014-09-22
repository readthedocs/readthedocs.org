from django.db import models

from guardian.shortcuts import get_objects_for_user

from projects import constants


class ProjectManager(models.Manager):

    def _filter_queryset(self, user, privacy_level):
        # Avoid circular import
        from projects.models import Project
        if isinstance(privacy_level, basestring):
            privacy_level = (privacy_level,)
        queryset = Project.objects.filter(privacy_level__in=privacy_level)
        if not user:
            return queryset
        else:
            # Hack around get_objects_for_user not supporting global perms
            global_access = user.has_perm('projects.view_project')
            if global_access:
                queryset = Project.objects.all()
        if user.is_authenticated():
            # Add in possible user-specific views
            user_queryset = get_objects_for_user(user, 'projects.view_project')
            queryset = user_queryset | queryset
        return queryset.filter()

    def live(self, *args, **kwargs):
        base_qs = self.filter(skip=False)
        return base_qs.filter(*args, **kwargs)

    def public(self, user=None, *args, **kwargs):
        """
        Query for projects, privacy_level == public
        """
        queryset = self._filter_queryset(user, privacy_level=constants.PUBLIC)
        return queryset.filter(*args, **kwargs)

    def protected(self, user=None, *args, **kwargs):
        """
        Query for projects, privacy_level != private
        """
        queryset = self._filter_queryset(user,
                                         privacy_level=(constants.PUBLIC,
                                                        constants.PROTECTED))
        return queryset.filter(*args, **kwargs)

    def private(self, user=None, *args, **kwargs):
        """
        Query for projects, privacy_level != private
        """
        queryset = self._filter_queryset(user, privacy_level=constants.PRIVATE)
        return queryset.filter(*args, **kwargs)


class VersionManager(models.Manager):

    def _filter_queryset(self, user, project, privacy_level, only_active):
        # Avoid circular import
        from builds.models import Version
        if isinstance(privacy_level, basestring):
            privacy_level = (privacy_level,)
        queryset = Version.objects.filter(privacy_level__in=privacy_level)
        # Remove this so we can use public() for all active public projects
        # if not user and not project:
            # return queryset
        if user and user.is_authenticated():
            # Add in possible user-specific views
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            queryset = user_queryset | queryset
        elif user:
            # Hack around get_objects_for_user not supporting global perms
            global_access = user.has_perm('builds.view_version')
            if global_access:
                queryset = Version.objects.all()
        if project:
            # Filter by project if requested
            queryset = queryset.filter(project=project)
        if only_active:
            queryset = queryset.filter(active=True)
        return queryset

    def active(self, user=None, project=None, *args, **kwargs):
        queryset = self._filter_queryset(
            user,
            project,
            privacy_level=(constants.PUBLIC, constants.PROTECTED,
                           constants.PRIVATE),
            only_active=True,
        )
        return queryset.filter(*args, **kwargs)

    def public(self, user=None, project=None, only_active=True, *args,
               **kwargs):
        queryset = self._filter_queryset(
            user,
            project,
            privacy_level=(constants.PUBLIC),
            only_active=only_active
        )
        return queryset.filter(*args, **kwargs)

    def protected(self, user=None, project=None, only_active=True, *args,
                  **kwargs):
        queryset = self._filter_queryset(
            user,
            project,
            privacy_level=(constants.PUBLIC, constants.PROTECTED),
            only_active=only_active
        )
        return queryset.filter(*args, **kwargs)

    def private(self, user=None, project=None, only_active=True, *args,
                **kwargs):
        queryset = self._filter_queryset(
            user,
            project,
            privacy_level=(constants.PRIVATE),
            only_active=only_active
        )
        return queryset.filter(*args, **kwargs)
