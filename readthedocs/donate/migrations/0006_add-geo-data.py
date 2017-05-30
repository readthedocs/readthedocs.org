# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations

from django_countries import countries


def add_data(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Country = apps.get_model("donate", "Country")
    for code, name in list(countries):
        Country.objects.get_or_create(country=code)


class Migration(migrations.Migration):

    dependencies = [
        ('donate', '0005_add-geo-filters'),
    ]

    operations = [
        migrations.RunPython(add_data),
    ]
