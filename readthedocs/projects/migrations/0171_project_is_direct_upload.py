from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("projects", "0170_project_max_build_media_size"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalproject",
            name="is_direct_upload",
            field=models.BooleanField(
                db_default=False,
                default=False,
                help_text="Read the Docs never builds this project, every version comes from an upload.",
                verbose_name="Built externally and uploaded",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="is_direct_upload",
            field=models.BooleanField(
                db_default=False,
                default=False,
                help_text="Read the Docs never builds this project, every version comes from an upload.",
                verbose_name="Built externally and uploaded",
            ),
        ),
    ]
