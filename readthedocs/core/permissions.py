# -*- coding: utf-8 -*-

"""Objects for User permission checks."""

from readthedocs.core.utils.extend import SettingsOverrideObject


class AdminPermissionBase:

    @classmethod
    def is_admin(cls, user, project):
        # This explicitly uses "user in project.users.all" so that
        # users on projects can be cached using prefetch_related or prefetch_related_objects
        return user in project.users.all() or user.is_superuser

    @classmethod
    def is_member(cls, user, obj):
        return user in obj.users.all() or user.is_superuser


class AdminPermission(SettingsOverrideObject):
    _default_class = AdminPermissionBase
    _override_setting = 'ADMIN_PERMISSION'
