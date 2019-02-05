# -*- coding: utf-8 -*-

"""Objects for User permission checks."""

from readthedocs.core.utils.extend import SettingsOverrideObject


class AdminPermissionBase:

    @classmethod
    def is_admin(cls, user, project):
        return user in project.users.all() or user.is_superuser

    @classmethod
    def is_member(cls, user, obj):
        return user in obj.users.all() or user.is_superuser


class AdminPermission(SettingsOverrideObject):
    _default_class = AdminPermissionBase
    _override_setting = 'ADMIN_PERMISSION'
