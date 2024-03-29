# Generated by Django 4.2.6 on 2023-10-18 11:43

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("builds", "0053_alter_version_build_data"),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name="build",
            index_together={
                ("date", "id"),
                ("version", "state", "type"),
                ("version", "state", "date", "success"),
            },
        ),
    ]
