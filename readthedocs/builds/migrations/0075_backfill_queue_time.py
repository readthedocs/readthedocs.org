import datetime

from django.db import migrations
from django_safemigrate import Safe


# Builds created this year (2026); ``task_executed_at`` was added on
# 2025-09-30, so only recent builds have it populated and can be backfilled.
BACKFILL_SINCE = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
BATCH_SIZE = 5000


def forward_backfill_queue_time(apps, schema_editor):
    """
    Backfill ``queue_time`` for builds triggered this year.

    The queued time is the number of seconds between when the build was
    triggered (``date``) and when the task started running on a builder
    (``task_executed_at``). Computed in Python and written in batches to avoid
    a single large UPDATE locking the table.
    """
    Build = apps.get_model("builds", "Build")
    queryset = (
        Build.objects.filter(
            date__gte=BACKFILL_SINCE,
            task_executed_at__isnull=False,
            queue_time__isnull=True,
        )
        .only("id", "date", "task_executed_at")
        .order_by("pk")
    )

    batch = []
    for build in queryset.iterator():
        build.queue_time = int((build.task_executed_at - build.date).total_seconds())
        batch.append(build)
        if len(batch) >= BATCH_SIZE:
            Build.objects.bulk_update(batch, ["queue_time"])
            batch = []
    if batch:
        Build.objects.bulk_update(batch, ["queue_time"])


class Migration(migrations.Migration):
    safe = Safe.after_deploy()

    dependencies = [
        ("builds", "0074_build_queue_time"),
    ]

    operations = [
        migrations.RunPython(
            forward_backfill_queue_time,
            migrations.RunPython.noop,
        ),
    ]
