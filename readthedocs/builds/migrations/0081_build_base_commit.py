from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()
    dependencies = [
        ("builds", "0080_version_ordering_ascending"),
    ]

    operations = [
        migrations.AddField(
            model_name="build",
            name="base_commit",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Base commit",
            ),
        ),
    ]
