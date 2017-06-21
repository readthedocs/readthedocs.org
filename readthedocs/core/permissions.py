"""Objects for User permission checks"""

from __future__ import absolute_import

from readthedocs.core.utils.extend import SettingsOverrideObject


class AdminPermissionBase(object):

    @classmethod
    def is_admin(cls, user, project):
        return user in project.users.all()

    @classmethod
    def is_member(cls, user, obj):
        return user in obj.users.all()


class AdminPermission(SettingsOverrideObject):
    _default_class = AdminPermissionBase
    _override_setting = 'ADMIN_PERMISSION'
