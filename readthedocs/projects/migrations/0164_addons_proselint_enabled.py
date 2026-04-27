from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("projects", "0163_automationrule_data_migration"),
    ]

    operations = [
        migrations.AddField(
            model_name="addonsconfig",
            name="proselint_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="historicaladdonsconfig",
            name="proselint_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
