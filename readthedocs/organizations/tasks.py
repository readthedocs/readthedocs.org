"""Organization's tasks related."""

import logging

from readthedocs.builds.models import Build
from readthedocs.worker import app


log = logging.getLogger(__name__)


@app.task(queue='web')
def mark_organization_assets_not_cleaned(build_pk):
    """Mark an organization as `artifacts_cleaned=False`."""
    try:
        build = Build.objects.get(pk=build_pk)
    except Build.DoesNotExist:
        log.info("Build does not exist. build=%s", build_pk)
        return

    organization = build.project.organizations.first()
    if organization:
        log.info("Marking organization as not cleaned. organization=%s", organization.slug)
        organization.artifacts_cleaned = False
        organization.save()
