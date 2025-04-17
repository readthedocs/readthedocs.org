# Generated by Django 2.2.24 on 2021-08-17 14:54
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("organizations", "0005_historicalorganization_historicalteam"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalorganization",
            name="artifacts_cleaned",
            field=models.BooleanField(
                default=False,
                help_text="Artifacts are cleaned out from storage",
                verbose_name="Artifacts Cleaned",
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="artifacts_cleaned",
            field=models.BooleanField(
                default=False,
                help_text="Artifacts are cleaned out from storage",
                verbose_name="Artifacts Cleaned",
            ),
        ),
    ]
