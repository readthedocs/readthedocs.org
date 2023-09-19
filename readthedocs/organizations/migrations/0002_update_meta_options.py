# Generated by Django 2.2.11 on 2020-03-12 17:37

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_squashed"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="organization",
            options={
                "base_manager_name": "objects",
                "get_latest_by": ["-pub_date"],
                "ordering": ["name"],
            },
        ),
        migrations.AlterModelOptions(
            name="team",
            options={"base_manager_name": "objects"},
        ),
    ]
