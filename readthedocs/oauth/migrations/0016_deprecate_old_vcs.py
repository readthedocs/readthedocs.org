# Generated by Django 4.2.13 on 2024-06-10 10:29

import django.core.validators
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()
    dependencies = [
        ("oauth", "0015_increase_avatar_url_length"),
    ]

    operations = [
        migrations.AlterField(
            model_name="remoterepository",
            name="clone_url",
            field=models.URLField(
                blank=True,
                max_length=512,
                validators=[
                    django.core.validators.URLValidator(schemes=["http", "https", "ssh", "git"])
                ],
                verbose_name="Repository clone URL",
            ),
        ),
        migrations.AlterField(
            model_name="remoterepository",
            name="vcs",
            field=models.CharField(
                blank=True, choices=[("git", "Git")], max_length=200, verbose_name="vcs"
            ),
        ),
    ]
