"""A namespace of privacy classes configured by settings.

Importing classes from this module allows the classes used to be overridden
using Django settings.

"""

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.privacy import backend


# Managers
from readthedocs.privacy.backends import syncers


class ProjectManager(SettingsOverrideObject):
    _default_class = backend.ProjectManager
    _override_setting = 'PROJECT_MANAGER'


# VersionQuerySet was replaced by SettingsOverrideObject
class VersionManager(SettingsOverrideObject):
    _default_class = backend.VersionManager
    _override_setting = 'VERSION_MANAGER'


class BuildManager(SettingsOverrideObject):
    _default_class = backend.BuildManager
    _override_setting = 'BUILD_MANAGER'


class RelatedProjectManager(SettingsOverrideObject):
    _default_class = backend.RelatedProjectManager
    _override_setting = 'RELATED_PROJECT_MANAGER'


class RelatedBuildManager(SettingsOverrideObject):
    _default_class = backend.RelatedBuildManager
    _override_setting = 'RELATED_BUILD_MANAGER'


class RelatedUserManager(SettingsOverrideObject):
    _default_class = backend.RelatedUserManager
    _override_setting = 'RELATED_USER_MANAGER'


class ChildRelatedProjectManager(SettingsOverrideObject):
    _default_class = backend.ChildRelatedProjectManager
    _override_setting = 'CHILD_RELATED_PROJECT_MANAGER'


# Permissions
class AdminPermission(SettingsOverrideObject):
    _default_class = backend.AdminPermission
    _override_setting = 'ADMIN_PERMISSION'


# Syncers
class Syncer(SettingsOverrideObject):
    _default_class = syncers.LocalSyncer
    _override_setting = 'FILE_SYNCER'
