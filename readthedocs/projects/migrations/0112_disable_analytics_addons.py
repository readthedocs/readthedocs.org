# Generated by Django 4.2.9 on 2024-01-23 16:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0111_add_multiple_versions_without_translations"),
    ]

    operations = [
        migrations.AlterField(
            model_name="addonsconfig",
            name="analytics_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
