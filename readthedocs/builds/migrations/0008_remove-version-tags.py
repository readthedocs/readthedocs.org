# Generated by Django 1.11.20 on 2019-06-28 16:29
from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("builds", "0007_add-automation-rules"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="version",
            name="tags",
        ),
    ]
