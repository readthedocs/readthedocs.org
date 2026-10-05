from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()
    dependencies = [
        ("builds", "0076_version_is_uploaded"),
    ]

    operations = [
        migrations.AddField(
            model_name="build",
            name="dispatched_date",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Dispatched date",
            ),
        ),
    ]
