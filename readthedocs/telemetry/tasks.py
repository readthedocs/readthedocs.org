"""Tasks related to telemetry."""

from django.conf import settings
from django.db import connections
from django.utils import timezone

from readthedocs.builds.models import Build
from readthedocs.telemetry.models import BuildData
from readthedocs.worker import app


@app.task(queue="web")
def save_build_data(build_id, data):
    """
    Save the build data asynchronously.

    Mainly used from the builders,
    since they don't have access to the database.
    """
    build = Build.objects.filter(id=build_id).first()
    if build:
        BuildData.objects.collect(build, data)


@app.task(queue="web")
def delete_old_build_data():
    """
    Delete BuildData models older than ``RTD_TELEMETRY_DATA_RETENTION_DAYS``.

    This is intended to run from a periodic task daily.

    NOTE: the logic of this task could be improved to keep longer data we care
          more (eg. active projects )and remove data we don't (eg. builds from spam projects)
    """
    retention_days = settings.RTD_TELEMETRY_DATA_RETENTION_DAYS
    days_ago = timezone.now().date() - timezone.timedelta(days=retention_days)
    # NOTE: we are using raw SQL here to avoid Django doing a SELECT first to
    # send `pre_` and `post_` delete signals
    # See https://docs.djangoproject.com/en/4.2/ref/models/querysets/#delete
    with connections["telemetry"].cursor() as cursor:
        cursor.execute(
            # "SELECT COUNT(*) FROM telemetry_builddata WHERE created BETWEEN %s AND %s",
            "DELETE FROM telemetry_builddata WHERE created BETWEEN %s AND %s",
            [
                days_ago - timezone.timedelta(days=90),
                days_ago,
            ],
        )
