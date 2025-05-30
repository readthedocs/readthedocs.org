# Generated by Django 3.2.19 on 2023-06-27 15:52
from django.db import migrations
from django_safemigrate import Safe


def forwards_func(apps, schema_editor):
    """Create ALLOW_VERSION_WARNING_BANNER feature flag and assign projects."""
    Project = apps.get_model("projects", "Project")
    Feature = apps.get_model("projects", "Feature")

    feature = Feature.objects.create(feature_id="allow_version_warning_banner")
    for project in Project.objects.filter(show_version_warning=True).iterator():
        feature.projects.add(project)


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0101_add_path_prefixes"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
