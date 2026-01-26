"""Tasks for Read the Docs' analytics."""

from django.conf import settings
from django.utils import timezone
from readthedocs.analytics.models import PageView

from readthedocs.worker import app


@app.task(queue="web")
def delete_old_page_counts():
    """
    Delete page counts older than ``RTD_ANALYTICS_DEFAULT_RETENTION_DAYS``.

    This is intended to run from a periodic task daily.
    """
    retention_days = settings.RTD_ANALYTICS_DEFAULT_RETENTION_DAYS
    days_ago = timezone.now().date() - timezone.timedelta(days=retention_days)

    # NOTE: We use _raw_delete to avoid Django fetching all objects
    # before the deletion. `pre_delete` and `post_delete` signals
    # won't be sent, this is fine as we don't have any special logic
    # for the PageView model.
    qs = PageView.objects.filter(date__lt=days_ago)
    qs._raw_delete(qs.db)
