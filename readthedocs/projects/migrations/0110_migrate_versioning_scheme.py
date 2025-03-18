# Generated by Django 4.2.5 on 2023-10-18 22:39
from django.db import migrations
from django_safemigrate import Safe


def forwards_func(apps, schema_editor):
    """Migrate single version projects to new versioning scheme field."""
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(single_version=True).update(
        versioning_scheme="single_version_without_translations",
        # Set this field to false, so we always rely on the versioning scheme field instead.
        single_version=False,
    )
    # Migrate projects that were created before the versioning scheme field was added.
    Project.objects.filter(versioning_scheme=None).update(
        versioning_scheme="multiple_versions_with_translations"
    )


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("projects", "0109_add_project_versioning_scheme"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
