# Generated by Django 4.2.16 on 2024-09-23 20:22

from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.always
    dependencies = [
        ("integrations", "0013_set_timestamp_fields_as_no_null"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="httpexchange",
            index=models.Index(
                fields=["content_type", "object_id", "date"],
                name="integration_content_5d4e98_idx",
            ),
        ),
    ]
