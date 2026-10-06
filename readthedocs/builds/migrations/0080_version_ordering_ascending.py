from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.always()

    dependencies = [
        ("builds", "0079_remove_version_uploaded"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="version",
            options={"ordering": ["verbose_name"]},
        ),
    ]
