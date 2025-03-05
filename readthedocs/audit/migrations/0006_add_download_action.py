# Generated by Django 2.2.24 on 2021-10-27 15:29
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("audit", "0005_migrate_ip_field_values"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("pageview", "Page view"),
                    ("download", "Download"),
                    ("authentication", "Authentication"),
                    ("authentication-failure", "Authentication failure"),
                    ("log-out", "Log out"),
                ],
                max_length=150,
                verbose_name="Action",
            ),
        ),
    ]
