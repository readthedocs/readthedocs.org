from django.conf import settings
from django.core.files.storage import get_storage_class
from django.shortcuts import get_object_or_404

from readthedocs.builds.models import Version


def wipe_version_via_slugs(version_slug, project_slug):
    """Wipes the given version of a given project."""
    version = get_object_or_404(
        Version,
        slug=version_slug,
        project__slug=project_slug,
    )

    # Delete the cache environment from storage
    storage = get_storage_class(settings.RTD_BUILD_ENVIRONMENT_STORAGE)()
    storage.delete(version.get_storage_environment_cache_path())
