from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0013_add-container-limits"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="has_valid_clone",
            field=models.BooleanField(
                default=False, help_text="This project has been successfully cloned"
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="has_valid_webhook",
            field=models.BooleanField(
                default=False, help_text="This project has been build with a webhook"
            ),
        ),
    ]
