from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0007_migrate_canonical_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectrelationship",
            name="alias",
            field=models.CharField(max_length=255, null=True, verbose_name="Alias", blank=True),
        ),
    ]
