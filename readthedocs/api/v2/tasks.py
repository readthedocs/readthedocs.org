from datetime import timedelta

import structlog
from django.utils import timezone

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.worker import app


log = structlog.get_logger(__name__)


@app.task(queue="web")
def delete_old_revoked_build_api_keys(days=15):
    """
    Delete revoked and expired keys that are older than x days.

    We don't delete keys created in the last 15 days,
    to have some audit trail in case we need to investigate something.
    """
    created_before = timezone.now() - timedelta(days=days)
    to_delete = BuildAPIKey.objects.filter(revoked=True, created__lt=created_before)
    log.info("Deleting revoked keys", count=to_delete.count())
    to_delete.delete()

    to_delete = BuildAPIKey.objects.filter(
        expiry_date__lt=timezone.now(), created__lt=created_before
    )
    log.info("Deleting expired keys", count=to_delete.count())
    to_delete.delete()
