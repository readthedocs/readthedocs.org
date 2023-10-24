# Generated by Django 4.2.5 on 2023-10-18 22:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0108_migrate_language_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalproject",
            name="versioning_scheme",
            field=models.CharField(
                choices=[
                    ("single_version", "Single version"),
                    ("multi_version", "Multi version"),
                ],
                default="multi_version",
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
                    ("single_version", "Single version"),
                    ("multi_version", "Multi version"),
                ],
                default="multi_version",
                help_text="This affects how the URL of your documentation looks like, and if it supports translations or multiple versions. Changing the versioning scheme will break your current URLs.",
                max_length=120,
                null=True,
                verbose_name="Versioning scheme",
            ),
        ),
    ]
