"""Celery tasks related to audit logs."""

import structlog
from django.conf import settings
from django.utils import timezone

from readthedocs.audit.models import AuditLog
from readthedocs.worker import app


log = structlog.get_logger(__name__)


@app.task(queue="web")
def delete_old_personal_audit_logs(days=None):
    """
    Delete personal security logs older than `days`.

    If `days` isn't given, default to ``RTD_AUDITLOGS_DEFAULT_RETENTION_DAYS``.

    We delete logs that aren't related to an organization,
    there are tasks in .com to delete those according to their plan.
    """
    days = days or settings.RTD_AUDITLOGS_DEFAULT_RETENTION_DAYS
    days_ago = timezone.now() - timezone.timedelta(days=days)
    audit_logs = AuditLog.objects.filter(
        log_organization_id__isnull=True,
        created__lt=days_ago,
    )
    log.info("Deleting old audit logs.", days=days, count=audit_logs.count())
    audit_logs.delete()
