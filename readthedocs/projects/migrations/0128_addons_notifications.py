# Generated by Django 4.2.16 on 2024-10-29 14:05

from django.db import migrations, models
from django_safemigrate import Safe


def forward_add_fields(apps, schema_editor):
    AddonsConfig = apps.get_model("projects", "AddonsConfig")
    for addons in AddonsConfig.objects.filter(project__isnull=False):
        addons.notifications_show_on_latest = (
            addons.stable_latest_version_warning_enabled
        )
        addons.notifications_show_on_non_stable = (
            addons.stable_latest_version_warning_enabled
        )
        addons.notifications_show_on_external = (
            addons.external_version_warning_enabled
        )
        addons.save()


def reverse_remove_fields(apps, schema_editor):
    AddonsConfig = apps.get_model("projects", "AddonsConfig")
    for addons in AddonsConfig.objects.filter(project__isnull=False):
        addons.stable_latest_version_warning_enabled = (
            addons.notifications_show_on_latest
            or addons.notifications_show_on_non_stable
        )
        addons.external_version_warning_enabled = addons.notifications_show_on_external
        addons.save()


class Migration(migrations.Migration):
    safe = Safe.before_deploy

    dependencies = [
        ("projects", "0127_default_to_semver"),
    ]

    operations = [
        migrations.AddField(
            model_name="addonsconfig",
            name="notifications_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="addonsconfig",
            name="notifications_show_on_external",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="addonsconfig",
            name="notifications_show_on_latest",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="addonsconfig",
            name="notifications_show_on_non_stable",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="historicaladdonsconfig",
            name="notifications_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="historicaladdonsconfig",
            name="notifications_show_on_external",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="historicaladdonsconfig",
            name="notifications_show_on_latest",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="historicaladdonsconfig",
            name="notifications_show_on_non_stable",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(forward_add_fields, reverse_remove_fields),
    ]
