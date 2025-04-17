# Generated by Django 3.2.20 on 2023-08-01 13:21
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("core", "0013_add_optout_email_config_file_deprecation"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicaluserprofile",
            name="optout_email_build_image_deprecation",
            field=models.BooleanField(
                default=False,
                null=True,
                verbose_name="Opt-out from email about '\"build.image\" config key deprecation'",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="optout_email_build_image_deprecation",
            field=models.BooleanField(
                default=False,
                null=True,
                verbose_name="Opt-out from email about '\"build.image\" config key deprecation'",
            ),
        ),
    ]
