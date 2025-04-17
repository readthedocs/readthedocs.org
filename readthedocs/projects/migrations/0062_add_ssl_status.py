# Generated by Django 2.2.14 on 2020-08-20 18:13
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0061_add_imported_file_ignore"),
    ]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="ssl_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("valid", "Valid and active"),
                    ("invalid", "Invalid"),
                    ("pending", "Pending"),
                    ("unknown", "Unknown"),
                ],
                default="unknown",
                max_length=30,
                null=True,
                verbose_name="SSL certificate status",
            ),
        ),
    ]
