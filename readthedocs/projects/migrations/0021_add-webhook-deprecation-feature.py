"""Add feature for allowing access to deprecated webhook endpoints."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0020_add-api-project-proxy"),
    ]

    operations = []
