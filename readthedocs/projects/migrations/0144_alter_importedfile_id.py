from django.db import migrations, models


class Migration(migrations.Migration):

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
