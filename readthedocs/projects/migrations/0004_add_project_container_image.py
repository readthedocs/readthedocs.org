from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0003_project_cdn_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="container_image",
            field=models.CharField(
                max_length=64,
                null=True,
                verbose_name="Alternative container image",
                blank=True,
            ),
        ),
    ]
