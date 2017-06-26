# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_migrate_canonical_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectrelationship',
            name='alias',
            field=models.CharField(max_length=255, null=True, verbose_name='Alias', blank=True),
        ),
    ]
