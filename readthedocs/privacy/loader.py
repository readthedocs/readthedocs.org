from django.utils.module_loading import import_string
from django.conf import settings

# Managers
ProjectManager = import_string(
    getattr(settings, 'PROJECT_MANAGER',
            'readthedocs.privacy.backend.ProjectManager'))
# VersionQuerySet was replaced by SettingsOverrideObject
VersionManager = import_string(
    getattr(settings, 'VERSION_MANAGER',
            'readthedocs.privacy.backend.VersionManager'))
BuildManager = import_string(
    getattr(settings, 'BUILD_MANAGER',
            'readthedocs.privacy.backend.BuildManager'))
RelatedProjectManager = import_string(
    getattr(settings, 'RELATED_PROJECT_MANAGER',
            'readthedocs.privacy.backend.RelatedProjectManager'))
RelatedBuildManager = import_string(
    getattr(settings, 'RELATED_BUILD_MANAGER',
            'readthedocs.privacy.backend.RelatedBuildManager'))
RelatedUserManager = import_string(
    getattr(settings, 'RELATED_USER_MANAGER',
            'readthedocs.privacy.backend.RelatedUserManager'))
ChildRelatedProjectManager = import_string(
    getattr(settings, 'CHILD_RELATED_PROJECT_MANAGER',
            'readthedocs.privacy.backend.ChildRelatedProjectManager'))

# Permissions
AdminPermission = import_string(
    getattr(settings, 'ADMIN_PERMISSION',
            'readthedocs.privacy.backend.AdminPermission'))

# Syncers
Syncer = import_string(
    getattr(settings, 'FILE_SYNCER',
            'readthedocs.privacy.backends.syncers.LocalSyncer'))
