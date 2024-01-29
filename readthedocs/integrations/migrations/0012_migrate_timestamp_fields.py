# Generated by Django 4.2.9 on 2024-01-29 19:16

from django.db import migrations
from django.utils import timezone


def forwards_func(apps, schema_editor):
    Integration = apps.get_model("integrations", "Integration")
    Integration.objects.filter(created=None).update(created=timezone.now())
    Integration.objects.filter(modified=None).update(modified=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0011_add_created_and_updated_fields"),
    ]

    operations = [migrations.RunPython(forwards_func)]
