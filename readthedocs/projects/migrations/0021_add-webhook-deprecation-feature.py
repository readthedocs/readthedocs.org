# -*- coding: utf-8 -*-

"""Add feature for allowing access to deprecated webhook endpoints."""

from django.db import migrations


FEATURE_ID = 'allow_deprecated_webhooks'


def forward_add_feature(apps, schema_editor):
    Feature = apps.get_model('projects', 'Feature')
    Feature.objects.create(
        feature_id=FEATURE_ID,
        default_true=True,
    )


def reverse_add_feature(apps, schema_editor):
    Feature = apps.get_model('projects', 'Feature')
    Feature.objects.filter(feature_id=FEATURE_ID).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0020_add-api-project-proxy'),
    ]

    operations = [
        migrations.RunPython(forward_add_feature, reverse_add_feature),
    ]
