"""Tasks for Read the Docs' analytics."""

from django.conf import settings
from django.db import connection
from django.utils import timezone

from readthedocs.worker import app


@app.task(queue="web")
def delete_old_page_counts():
    """
    Delete page counts older than ``RTD_ANALYTICS_DEFAULT_RETENTION_DAYS``.

    This is intended to run from a periodic task daily.
    """
    retention_days = settings.RTD_ANALYTICS_DEFAULT_RETENTION_DAYS
    days_ago = timezone.now().date() - timezone.timedelta(days=retention_days)

    # NOTE: we are using raw SQL here to avoid Django doing a SELECT first to
    # send `pre_` and `post_` delete signals
    # See https://docs.djangoproject.com/en/4.2/ref/models/querysets/#delete
    with connection.cursor() as cursor:
        cursor.execute(
            # "SELECT COUNT(*) FROM analytics_pageview WHERE date BETWEEN %s AND %s",
            "DELETE FROM analytics_pageview WHERE date BETWEEN %s AND %s",
            [
                days_ago - timezone.timedelta(days=90),
                days_ago,
            ],
        )
