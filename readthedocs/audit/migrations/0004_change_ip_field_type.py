# Generated by Django 2.2.24 on 2021-09-21 00:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0003_update_ordering"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="ip",
            field=models.CharField(
                blank=True, max_length=250, null=True, verbose_name="IP address"
            ),
        ),
    ]
