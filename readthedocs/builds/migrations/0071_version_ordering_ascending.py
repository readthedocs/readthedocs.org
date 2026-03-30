from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("builds", "0070_delete_build_old_config"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="version",
            options={"ordering": ["verbose_name"]},
        ),
    ]
