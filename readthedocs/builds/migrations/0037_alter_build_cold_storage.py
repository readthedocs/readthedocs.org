# Generated by Django 3.2.9 on 2021-11-26 11:05
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("builds", "0036_change_mkdocs_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="build",
            name="cold_storage",
            field=models.BooleanField(
                help_text="Build steps stored outside the database.",
                null=True,
                verbose_name="Cold Storage",
            ),
        ),
    ]
