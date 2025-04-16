# Generated by Django 4.2.5 on 2023-10-18 22:04
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0108_migrate_language_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalproject",
            name="versioning_scheme",
            field=models.CharField(
                choices=[
                    (
                        "multiple_versions_with_translations",
                        "Multiple versions with translations (/<language>/<version>/<filename>)",
                    ),
                    (
                        "single_version_without_translations",
                        "Single version without translations (/<filename>)",
                    ),
                ],
                default="multiple_versions_with_translations",
                help_text="This affects how the URL of your documentation looks like, and if it supports translations or multiple versions. Changing the versioning scheme will break your current URLs.",
                max_length=120,
                null=True,
                verbose_name="Versioning scheme",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="versioning_scheme",
            field=models.CharField(
                choices=[
                    (
                        "multiple_versions_with_translations",
                        "Multiple versions with translations (/<language>/<version>/<filename>)",
                    ),
                    (
                        "single_version_without_translations",
                        "Single version without translations (/<filename>)",
                    ),
                ],
                default="multiple_versions_with_translations",
                help_text="This affects how the URL of your documentation looks like, and if it supports translations or multiple versions. Changing the versioning scheme will break your current URLs.",
                max_length=120,
                null=True,
                verbose_name="Versioning scheme",
            ),
        ),
    ]
