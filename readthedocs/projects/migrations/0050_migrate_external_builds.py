# Generated by Django 2.2.10 on 2020-05-19 13:24

from django.db import migrations


def migrate_features(apps, schema_editor):
    # Enable the PR builder for projects with the feature flag
    Feature = apps.get_model("projects", "Feature")
    if Feature.objects.filter(feature_id="external_version_build").exists():
        for project in Feature.objects.get(
            feature_id="external_version_build"
        ).projects.all():
            project.external_builds_enabled = True
            project.save()


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0049_add_external_build_enabled"),
    ]

    operations = [
        migrations.RunPython(migrate_features),
    ]
