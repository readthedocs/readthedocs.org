from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0016_build-queue-name"),
    ]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="https",
            field=models.BooleanField(
                default=False,
                help_text="SSL is enabled for this domain",
                verbose_name="Use HTTPS",
            ),
        ),
    ]
