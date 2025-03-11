# Generated by Django 2.2.12 on 2020-04-23 16:42
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("projects", "0045_project_max_concurrent_builds"),
    ]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="hsts_include_subdomains",
            field=models.BooleanField(
                default=False,
                help_text="If hsts_max_age > 0, set the includeSubDomains flag with the HSTS header",
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="hsts_max_age",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Set a custom max-age (eg. 31536000) for the HSTS header",
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="hsts_preload",
            field=models.BooleanField(
                default=False,
                help_text="If hsts_max_age > 0, set the preload flag with the HSTS header",
            ),
        ),
    ]
