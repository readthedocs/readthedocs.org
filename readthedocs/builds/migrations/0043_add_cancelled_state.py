# Generated by Django 3.2.13 on 2022-05-04 11:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("builds", "0042_version_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="build",
            name="state",
            field=models.CharField(
                choices=[
                    ("triggered", "Triggered"),
                    ("cloning", "Cloning"),
                    ("installing", "Installing"),
                    ("building", "Building"),
                    ("uploading", "Uploading"),
                    ("finished", "Finished"),
                    ("cancelled", "Cancelled"),
                ],
                db_index=True,
                default="finished",
                max_length=55,
                verbose_name="State",
            ),
        ),
    ]
