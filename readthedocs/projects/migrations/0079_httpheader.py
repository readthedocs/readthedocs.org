import django.db.models.deletion
import django_extensions.db.fields

# Generated by Django 2.2.24 on 2021-07-26 10:35
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0078_add_external_builds_privacy_level_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="HTTPHeader",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        choices=[
                            ("referrer_policy", "Referrer-Policy"),
                            ("permissions_policy", "Permissions-Policy"),
                            ("feature_policy", "Feature-Policy"),
                            (
                                "access_control_allow_origin",
                                "Access-Control-Allow-Origin",
                            ),
                            (
                                "access_control_allow_headers",
                                "Access-Control-Allow-Headers",
                            ),
                            ("x_frame_options", "X-Frame-Options"),
                        ],
                        max_length=128,
                    ),
                ),
                ("value", models.CharField(max_length=256)),
                (
                    "only_if_secure_request",
                    models.BooleanField(
                        help_text="Only set this header if the request is secure (HTTPS)"
                    ),
                ),
                (
                    "domain",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="http_headers",
                        to="projects.Domain",
                    ),
                ),
            ],
            options={
                "get_latest_by": "modified",
                "abstract": False,
            },
        ),
    ]
