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
            name="build_method",
            field=models.CharField(
                choices=[
                    ("readthedocs", "Build on Read the Docs"),
                    ("direct_upload", "Build externally and upload"),
                ],
                db_default="readthedocs",
                default="readthedocs",
                help_text="Whether Read the Docs builds the documentation, or it is built externally and uploaded.",
                max_length=32,
                verbose_name="Build method",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="build_method",
            field=models.CharField(
                choices=[
                    ("readthedocs", "Build on Read the Docs"),
                    ("direct_upload", "Build externally and upload"),
                ],
                db_default="readthedocs",
                default="readthedocs",
                help_text="Whether Read the Docs builds the documentation, or it is built externally and uploaded.",
                max_length=32,
                verbose_name="Build method",
            ),
        ),
    ]
