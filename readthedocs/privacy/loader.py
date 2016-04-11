from django.utils.module_loading import import_by_path
from django.conf import settings

# Managers
ProjectManager = import_by_path(
    getattr(settings, 'PROJECT_MANAGER',
            'readthedocs.privacy.backend.ProjectManager'))
VersionManager = import_by_path(
    getattr(settings, 'VERSION_MANAGER',
            'readthedocs.privacy.backend.VersionManager'))
BuildManager = import_by_path(
    getattr(settings, 'BUILD_MANAGER',
            'readthedocs.privacy.backend.BuildManager'))

RelatedProjectManager = import_by_path(
    getattr(settings, 'RELATED_PROJECT_MANAGER',
            'readthedocs.privacy.backend.RelatedProjectManager'))
RelatedBuildManager = import_by_path(
    getattr(settings, 'RELATED_BUILD_MANAGER',
            'readthedocs.privacy.backend.RelatedBuildManager'))
RelatedUserManager = import_by_path(
    getattr(settings, 'RELATED_USER_MANAGER',
            'readthedocs.privacy.backend.RelatedUserManager'))
ChildRelatedProjectManager = import_by_path(
    getattr(settings, 'CHILD_RELATED_PROJECT_MANAGER',
            'readthedocs.privacy.backend.ChildRelatedProjectManager'))

# Permissions
AdminPermission = import_by_path(
    getattr(settings, 'ADMIN_PERMISSION',
            'readthedocs.privacy.backend.AdminPermission'))

# Syncers
Syncer = import_by_path(
    getattr(settings, 'FILE_SYNCER',
            'readthedocs.privacy.backends.syncers.LocalSyncer'))
