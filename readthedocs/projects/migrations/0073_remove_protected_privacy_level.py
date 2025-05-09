# Generated by Django 2.2.20 on 2021-04-29 18:49
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0072_remove_md5_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="privacy_level",
            field=models.CharField(
                choices=[("public", "Public"), ("private", "Private")],
                default="public",
                help_text="Should the project dashboard be public?",
                max_length=20,
                verbose_name="Privacy Level",
            ),
        ),
    ]
