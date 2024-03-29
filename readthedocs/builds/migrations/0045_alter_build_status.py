# Generated by Django 3.2.15 on 2022-10-06 09:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("builds", "0044_alter_version_documentation_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="build",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[("normal", "Normal")],
                default=None,
                max_length=32,
                null=True,
                verbose_name="Status",
            ),
        ),
    ]
