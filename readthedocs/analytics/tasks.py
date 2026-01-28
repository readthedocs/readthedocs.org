"""Tasks for Read the Docs' analytics."""

import logging

from django.conf import settings
from django.utils import timezone

from readthedocs.analytics.models import PageView
from readthedocs.analytics.parquet import ParquetAnalyticsExporter
from readthedocs.worker import app


logger = logging.getLogger(__name__)


@app.task(queue="web")
def export_pageviews_to_parquet():
    """
    Export pageview data from the previous day to Parquet files.

    This is intended to run from a periodic task daily.
    Stores the data in S3 as Parquet files for efficient querying.
    """
    from datetime import timedelta

    try:
        target_date = timezone.now().date() - timedelta(days=1)
        exporter = ParquetAnalyticsExporter()
        result = exporter.export_daily_pageviews(target_date)

        logger.info(
            f"Exported {result['total_records']} pageviews for {target_date} "
            f"to {len(result['files'])} file(s)"
        )

        return {
            "status": "success",
            "date": str(target_date),
            "total_records": result["total_records"],
            "files_created": len(result["files"]),
        }
    except Exception:
        logger.exception("Failed to export pageviews to parquet")
        raise


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
