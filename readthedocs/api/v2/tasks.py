from readthedocs.api.v2.models import BuildAPIKey
import structlog
from readthedocs.worker import app
from django.utils import timezone
from datetime import timedelta

log = structlog.get_logger(__name__)


@app.task(queue="web")
def delete_old_revoked_build_api_keys():
    """
    Delete revoked and expired keys that are older than 7 days.

    We don't delete keys created in the last 7 days,
    to have some audit trail in case we need to investigate something.
    """
    created_before = timezone.now() - timedelta(days=7)
    to_delete = BuildAPIKey.objects.filter(revoked=True, created__lt=created_before)
    log.info("Deleting revoked keys", count=to_delete.count())
    to_delete.delete()

    to_delete = BuildAPIKey.objects.filter(expiry_date__lt=timezone.now(), created__lt=created_before)
    log.info("Deleting expired keys", count=to_delete.count())
    to_delete.delete()
