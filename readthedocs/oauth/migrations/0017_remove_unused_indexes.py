# Generated by Django 4.2.17 on 2025-02-18 21:38

from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy

    dependencies = [
        ("oauth", "0016_deprecate_old_vcs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="remoterepository",
            name="remote_id",
            field=models.CharField(max_length=128),
        ),
    ]
