from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()

    dependencies = [
        ("projects", "0144_addons_blank_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importedfile",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
