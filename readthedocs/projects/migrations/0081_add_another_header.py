# Generated by Django 2.2.24 on 2021-08-02 21:04
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("projects", "0080_historicalproject"),
    ]

    operations = [
        migrations.AlterField(
            model_name="httpheader",
            name="name",
            field=models.CharField(
                choices=[
                    ("access_control_allow_origin", "Access-Control-Allow-Origin"),
                    ("access_control_allow_headers", "Access-Control-Allow-Headers"),
                    ("content_security_policy", "Content-Security-Policy"),
                    ("feature_policy", "Feature-Policy"),
                    ("permissions_policy", "Permissions-Policy"),
                    ("referrer_policy", "Referrer-Policy"),
                    ("x_frame_options", "X-Frame-Options"),
                ],
                max_length=128,
            ),
        ),
    ]
