from django.utils.module_loading import import_by_path
from django.conf import settings

# Managers
ProjectManager = import_by_path(getattr(settings, 'PROJECT_MANAGER', 'privacy.backend.ProjectManager'))
VersionManager = import_by_path(getattr(settings, 'VERSION_MANAGER', 'privacy.backend.VersionManager'))
RelatedProjectManager = import_by_path(getattr(settings, 'RELATED_PROJECT_MANAGER', 'privacy.backend.RelatedProjectManager'))

# Permissions
AdminPermission = import_by_path(getattr(settings, 'ADMIN_PERMISSION', 'privacy.backend.AdminPermission'))

# Syncers
Syncer = import_by_path(getattr(settings, 'FILE_SYNCER', 'privacy.backends.syncers.LocalSyncer'))
