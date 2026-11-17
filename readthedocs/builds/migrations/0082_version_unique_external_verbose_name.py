from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("builds", "0081_merge_duplicate_external_versions"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="version",
            constraint=models.UniqueConstraint(
                condition=models.Q(("type", "external")),
                fields=("project", "verbose_name"),
                name="builds_version_unique_external_verbose_name",
            ),
        ),
    ]
