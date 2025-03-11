# Generated by Django 2.2.12 on 2020-06-10 17:11
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("projects", "0055_change_help_text_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="analytics_disabled",
            field=models.BooleanField(
                default=False,
                help_text="Disable Google Analytics completely for this project (requires rebuilding documentation)",
                null=True,
                verbose_name="Disable Analytics",
            ),
        ),
    ]
