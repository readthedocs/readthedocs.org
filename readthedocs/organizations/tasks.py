import logging

from readthedocs.worker import app


log = logging.getLogger(__name__)


@app.task(queue='web')
def mark_organization_assets_not_cleaned(organization):
    log.info("Marking organization as not cleaned. organization=%s", organization.slug)
    organization.artifacts_cleaned = False
    organization.save()
