from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.always()

    dependencies = [
        ("builds", "0072_remove_deprecated_build_fields"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="version",
            options={"ordering": ["verbose_name"]},
        ),
    ]
