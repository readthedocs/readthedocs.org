# Generated by Django 3.2.11 on 2022-01-26 20:10
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("builds", "0040_remove_old_jsonfields"),
    ]

    operations = [
        migrations.AddField(
            model_name="build",
            name="task_id",
            field=models.CharField(
                blank=True, max_length=36, null=True, verbose_name="Celery task id"
            ),
        ),
    ]
