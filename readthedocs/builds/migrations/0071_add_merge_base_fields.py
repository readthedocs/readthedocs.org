# Generated for filetreediff merge-base tracking.

from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("builds", "0070_delete_build_old_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="version",
            name="base_branch",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Base branch",
            ),
        ),
        migrations.AddField(
            model_name="build",
            name="merge_base",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Merge base",
            ),
        ),
    ]
