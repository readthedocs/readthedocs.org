
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

    """
    Projects take into account their own privacy_level setting.
    """

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user):
        if user.has_perm('projects.view_project'):
            return self.get_queryset().all().distinct()
        if user.is_authenticated():
            user_queryset = get_objects_for_user(user, 'projects.view_project')
            queryset = user_queryset | queryset
        return queryset.distinct()

    def for_user_and_viewer(self, user, viewer):
        """
        Show projects that a user owns, that another user can see.
        """
        queryset = self.filter(privacy_level=constants.PUBLIC)
        queryset = self._add_user_repos(queryset, viewer)
        queryset = queryset.filter(users__in=[user])
        return queryset

    def for_admin_user(self, user=None):
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

    def protected(self, user=None):
        queryset = self.filter(privacy_level__in=[constants.PUBLIC, constants.PROTECTED])
        if user:
            return self._add_user_repos(queryset, user)
        else:
            return queryset

    def private(self, user=None):
        queryset = self.filter(privacy_level=constants.PRIVATE)
        if user:
            return self._add_user_repos(queryset, user)
        else:
            return queryset

    # Aliases

    def dashboard(self, user=None):
        return self.for_admin_user(user)

    def api(self, user=None):
        return self.public(user)


class VersionManager(models.Manager):

    """
    Versions take into account their own privacy_level setting.
    """

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user):
        if user.has_perm('builds.view_version'):
            return self.get_queryset().all().distinct()
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


class BuildManager(models.Manager):

    """
    Build objects take into account the privacy of the Version they relate to.
    """

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user=None):
        if user.has_perm('builds.view_version'):
            return self.get_queryset().all().distinct()
        if user.is_authenticated():
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            pks = [p.pk for p in user_queryset]
            queryset = self.get_queryset().filter(version__pk__in=pks) | queryset
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


class RelatedProjectManager(models.Manager):

    """
    A manager for things that relate to Project and need to get their perms from the project.

    This shouldn't be used as a subclass.
    """
    use_for_related_fields = True
    project_field = 'project'

    def _add_user_repos(self, queryset, user=None):
        # Hack around get_objects_for_user not supporting global perms
        if user.has_perm('projects.view_project'):
            return self.get_queryset().all().distinct()
        if user.is_authenticated():
            # Add in possible user-specific views
            project_qs = get_objects_for_user(user, 'projects.view_project')
            pks = [p.pk for p in project_qs]
            kwargs = {'%s__pk__in' % self.project_field: pks}
            queryset = self.get_queryset().filter(**kwargs) | queryset
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


class ParentRelatedProjectManager(RelatedProjectManager):
    project_field = 'parent'
    use_for_related_fields = True


class ChildRelatedProjectManager(RelatedProjectManager):
    project_field = 'child'
    use_for_related_fields = True


class RelatedBuildManager(models.Manager):

    '''For models with association to a project through :py:cls:`Build`'''

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user=None):
        if user.has_perm('builds.view_version'):
            return self.get_queryset().all().distinct()
        if user.is_authenticated():
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            pks = [p.pk for p in user_queryset]
            queryset = self.get_queryset().filter(
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


class RelatedUserManager(models.Manager):

    """For models with relations through :py:cls:`User`"""

    def api(self, user=None):
        """Return objects for user"""
        if not user.is_authenticated():
            return self.none()
        return self.filter(users=user)


class AdminPermission(object):

    @classmethod
    def is_admin(cls, user, project):
        return user in project.users.all()

    @classmethod
    def is_member(cls, user, obj):
        return user in obj.users.all()


class AdminNotAuthorized(ValueError):
    pass
