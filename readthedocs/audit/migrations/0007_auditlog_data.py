# Generated by Django 3.2.15 on 2022-09-15 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0006_add_download_action"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="data",
            field=models.JSONField(
                blank=True,
                help_text="Extra data about the log entry. Its structure depends on the type of log entry.",
                null=True,
            ),
        ),
    ]
