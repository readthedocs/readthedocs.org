from django.db import migrations, models
from django_safemigrate import Safe


class Migration(migrations.Migration):

    safe = Safe.after_deploy

    dependencies = [
        ("projects", "0143_addons_flyout_position"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importedfile",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
