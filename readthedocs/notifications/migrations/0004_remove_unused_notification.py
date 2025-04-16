# Generated by Django 4.2.16 on 2024-10-29 16:27

from django.db import migrations
from django_safemigrate import Safe


def remove_unused_notification(apps, schema_editor):
    Notification = apps.get_model("notifications", "Notification")
    Notification.objects.filter(message_id="oauth:deploy-key:attached-successfully").delete()


class Migration(migrations.Migration):
    safe = Safe.after_deploy()

    dependencies = [
        ("notifications", "0003_notification_indexes"),
    ]

    operations = [
        migrations.RunPython(remove_unused_notification),
    ]
