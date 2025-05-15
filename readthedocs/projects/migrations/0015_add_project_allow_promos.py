from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0014_add-state-tracking"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="allow_promos",
            field=models.BooleanField(
                default=True,
                help_text="Allow sponsor advertisements on my project documentation",
                verbose_name="Sponsor advertisements",
            ),
        ),
    ]
