"""Add feature for allowing access to deprecated webhook endpoints."""

from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0020_add-api-project-proxy"),
    ]

    operations = []
