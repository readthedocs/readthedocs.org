# Generated by Django 2.2.14 on 2020-07-13 20:00

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0057_add_page_rank"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="environmentvariable",
            options={"get_latest_by": "modified"},
        ),
    ]
