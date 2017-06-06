"""A namespace of privacy classes configured by settings.

Importing classes from this module allows the classes used to be overridden
using Django settings.

"""

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.privacy import backend


# Managers
from readthedocs.privacy.backends import syncers


class ProjectQuerySet(SettingsOverrideObject):
    _default_class = backend.ProjectQuerySet
    _override_setting = 'PROJECT_MANAGER'


# VersionQuerySet was replaced by SettingsOverrideObject
class VersionManager(SettingsOverrideObject):
    _default_class = backend.VersionManager
    _override_setting = 'VERSION_MANAGER'


class BuildQuerySet(SettingsOverrideObject):
    _default_class = backend.BuildQuerySet
    _override_setting = 'BUILD_MANAGER'


class RelatedProjectQuerySet(SettingsOverrideObject):
    _default_class = backend.RelatedProjectQuerySet
    _override_setting = 'RELATED_PROJECT_MANAGER'


class RelatedBuildQuerySet(SettingsOverrideObject):
    _default_class = backend.RelatedBuildQuerySet
    _override_setting = 'RELATED_BUILD_MANAGER'


class RelatedUserQuerySet(SettingsOverrideObject):
    _default_class = backend.RelatedUserQuerySet
    _override_setting = 'RELATED_USER_MANAGER'


class ChildRelatedProjectQuerySet(SettingsOverrideObject):
    _default_class = backend.ChildRelatedProjectQuerySet
    _override_setting = 'CHILD_RELATED_PROJECT_MANAGER'


# Permissions
class AdminPermission(SettingsOverrideObject):
    _default_class = backend.AdminPermission
    _override_setting = 'ADMIN_PERMISSION'


# Syncers
class Syncer(SettingsOverrideObject):
    _default_class = syncers.LocalSyncer
    _override_setting = 'FILE_SYNCER'
