from django.shortcuts import get_object_or_404

from readthedocs.builds.models import Version
from readthedocs.storage import build_environment_storage


def wipe_version_via_slugs(version_slug, project_slug):
    """Wipes the given version of a given project."""
    version = get_object_or_404(
        Version,
        slug=version_slug,
        project__slug=project_slug,
    )

    # Delete the cache environment from storage
    build_environment_storage.delete(version.get_storage_environment_cache_path())
