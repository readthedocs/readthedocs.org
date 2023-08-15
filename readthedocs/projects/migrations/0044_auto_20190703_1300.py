# Generated by Django 1.11.21 on 2019-07-03 13:00
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0043_add-build-field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="privacy_level",
            field=models.CharField(
                choices=[
                    ("public", "Public"),
                    ("protected", "Protected"),
                    ("private", "Private"),
                ],
                default="public",
                help_text="Level of privacy that you want on the repository.",
                max_length=20,
                verbose_name="Privacy Level",
            ),
        ),
    ]
