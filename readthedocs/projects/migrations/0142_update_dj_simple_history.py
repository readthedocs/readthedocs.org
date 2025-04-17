# Generated by Django 4.2.16 on 2024-11-27 19:39
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("projects", "0141_create_addonsconfig"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="historicaladdonsconfig",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical addons config",
                "verbose_name_plural": "historical addons configs",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalproject",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical project",
                "verbose_name_plural": "historical projects",
            },
        ),
        migrations.AlterField(
            model_name="historicaladdonsconfig",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalproject",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
    ]
