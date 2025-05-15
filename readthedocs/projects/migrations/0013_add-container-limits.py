from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0012_proper-name-for-install-project"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="build_queue",
            field=models.CharField(
                max_length=32,
                null=True,
                verbose_name="Alternate build queue id",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="container_mem_limit",
            field=models.CharField(
                help_text="Memory limit in Docker format -- example: <code>512m</code> or <code>1g</code>",
                max_length=10,
                null=True,
                verbose_name="Container memory limit",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="container_time_limit",
            field=models.CharField(
                max_length=10,
                null=True,
                verbose_name="Container time limit",
                blank=True,
            ),
        ),
    ]
