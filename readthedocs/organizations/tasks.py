"""Organization's tasks related."""

import structlog

from readthedocs.builds.models import Build
from readthedocs.worker import app


log = structlog.get_logger(__name__)


@app.task(queue="web")
def mark_organization_assets_not_cleaned(build_pk):
    """Mark an organization as `artifacts_cleaned=False`."""
    try:
        build = Build.objects.get(pk=build_pk)
    except Build.DoesNotExist:
        log.debug("Build does not exist.", build_pk=build_pk)
        return

    organization = build.project.organizations.first()
    if organization and organization.artifacts_cleaned:
        log.info("Marking organization as not cleaned.", origanization_slug=organization.slug)
        organization.artifacts_cleaned = False
        organization.save()
