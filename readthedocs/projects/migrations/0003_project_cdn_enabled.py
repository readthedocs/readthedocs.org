from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0002_add_importedfile_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="cdn_enabled",
            field=models.BooleanField(default=False, verbose_name="CDN Enabled"),
        ),
    ]
