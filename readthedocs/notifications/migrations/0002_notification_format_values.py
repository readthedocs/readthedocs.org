# Generated by Django 4.2.7 on 2023-11-29 15:44
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="format_values",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
