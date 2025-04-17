from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0010_migrate_domain_data"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="domain",
            name="url",
        ),
    ]
