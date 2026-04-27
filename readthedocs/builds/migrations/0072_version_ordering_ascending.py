from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.always()

    dependencies = [
        ("builds", "0071_alter_versionautomationrule_fk"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="version",
            options={"ordering": ["verbose_name"]},
        ),
    ]
