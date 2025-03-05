# Generated by Django 2.2.16 on 2020-11-05 22:05
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("oauth", "0010_index_full_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="remoterepository",
            name="default_branch",
            field=models.CharField(
                blank=True,
                max_length=150,
                null=True,
                verbose_name="Default branch of the repository",
            ),
        ),
    ]
