# Generated by Django 1.11.27 on 2020-02-17 18:14
import jsonfield.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0005_change_default_integration_secret"),
    ]

    operations = [
        migrations.AlterField(
            model_name="integration",
            name="provider_data",
            field=jsonfield.fields.JSONField(
                default=dict, verbose_name="Provider data"
            ),
        ),
    ]
