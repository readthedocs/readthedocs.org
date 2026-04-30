from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("builds", "0071_alter_versionautomationrule_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="version",
            name="source_type",
            field=models.CharField(
                choices=[("vcs", "VCS"), ("upload", "Pre-built upload")],
                default="vcs",
                max_length=16,
                verbose_name="Source type",
            ),
        ),
        migrations.AddField(
            model_name="version",
            name="upload_content_hash",
            field=models.CharField(
                blank=True,
                max_length=64,
                null=True,
                verbose_name="Upload content hash",
            ),
        ),
    ]
