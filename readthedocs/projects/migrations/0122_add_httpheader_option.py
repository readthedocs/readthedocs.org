# Generated by Django 4.2.11 on 2024-03-26 10:17

from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0121_remove_requirements_file"),
    ]

    operations = [
        migrations.AlterField(
            model_name="httpheader",
            name="name",
            field=models.CharField(
                choices=[
                    ("access_control_allow_origin", "Access-Control-Allow-Origin"),
                    ("access_control_allow_headers", "Access-Control-Allow-Headers"),
                    ("access_control_expose_headers", "Access-Control-Expose-Headers"),
                    ("content_security_policy", "Content-Security-Policy"),
                    ("feature_policy", "Feature-Policy"),
                    ("permissions_policy", "Permissions-Policy"),
                    ("referrer_policy", "Referrer-Policy"),
                    ("x_frame_options", "X-Frame-Options"),
                    ("x_content_type_options", "X-Content-Type-Options"),
                ],
                max_length=128,
            ),
        ),
    ]
