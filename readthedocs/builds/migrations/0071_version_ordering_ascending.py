from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.always()

    dependencies = [
        ("builds", "0070_delete_build_old_config"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="version",
            options={"ordering": ["verbose_name"]},
        ),
    ]
