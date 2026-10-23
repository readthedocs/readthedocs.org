from django.db import migrations
from django.db.models import OuterRef
from django.db.models import Subquery
from django_safemigrate import Safe


EXTERNAL = "external"


def forward(apps, schema_editor):
    """
    Point ``latest_build`` to the latest non-pull-request build.

    Previously, ``latest_build`` was updated for every build,
    including builds from pull request versions,
    but the dashboard only shows builds from non-pull-request versions.
    """
    Project = apps.get_model("projects", "Project")
    Build = apps.get_model("builds", "Build")

    latest_internal_build = (
        Build.objects.filter(project=OuterRef("pk"))
        .exclude(version__type=EXTERNAL)
        .order_by("-date")
        .values("pk")[:1]
    )
    Project.objects.filter(latest_build__version__type=EXTERNAL).update(
        latest_build=Subquery(latest_internal_build),
    )


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("builds", "0080_version_ordering_ascending"),
        ("projects", "0172_update_docs_links_in_help_text"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
