# Generated by Django 2.2.17 on 2021-01-12 22:39
from django.db import migrations
from django.db import models
from django_safemigrate import Safe

import readthedocs.projects.models


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0077_remote_repository_data_migration"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="external_builds_privacy_level",
            field=models.CharField(
                choices=[("public", "Public"), ("private", "Private")],
                default=readthedocs.projects.models.default_privacy_level,
                help_text="Should builds from pull requests be public?",
                max_length=20,
                null=True,
                verbose_name="Privacy level of Pull Requests",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="external_builds_enabled",
            field=models.BooleanField(
                default=False,
                help_text='More information in <a href="https://docs.readthedocs.io/page/guides/autobuild-docs-for-pull-requests.html">our docs</a>',
                verbose_name="Build pull requests for this project",
            ),
        ),
    ]
