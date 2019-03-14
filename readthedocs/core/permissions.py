# -*- coding: utf-8 -*-

"""Objects for User permission checks."""

from readthedocs.core.utils.extend import SettingsOverrideObject


class AdminPermissionBase:

    @classmethod
    def is_admin(cls, user, project):
        return user.is_superuser or project.users.filter(pk=user.pk).exists()

    @classmethod
    def is_member(cls, user, obj):
        return user.is_superuser or obj.users.filter(pk=user.pk).exists()


class AdminPermission(SettingsOverrideObject):
    _default_class = AdminPermissionBase
    _override_setting = 'ADMIN_PERMISSION'
