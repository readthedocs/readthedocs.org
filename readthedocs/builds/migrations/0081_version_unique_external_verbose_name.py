from django.db import migrations
from django.db import models
from django.db.models import Count
from django.db.models import Min
from django_safemigrate import Safe


def forwards_func(apps, schema_editor):
    """Keep the oldest external version for each pull request and move builds to it."""
    Version = apps.get_model("builds", "Version")
    Build = apps.get_model("builds", "Build")
    duplicates = (
        Version.objects.filter(type="external")
        .values("project", "verbose_name")
        .annotate(count=Count("id"), keep=Min("id"))
        .filter(count__gt=1)
    )
    for result in duplicates:
        extra = Version.objects.filter(
            project=result["project"],
            verbose_name=result["verbose_name"],
            type="external",
        ).exclude(id=result["keep"])
        Build.objects.filter(version__in=extra).update(version_id=result["keep"])
        extra.delete()


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("builds", "0080_version_ordering_ascending"),
    ]

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="version",
            constraint=models.UniqueConstraint(
                condition=models.Q(("type", "external")),
                fields=("project", "verbose_name"),
                name="builds_version_unique_external_verbose_name",
            ),
        ),
    ]
