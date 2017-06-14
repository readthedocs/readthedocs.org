# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_add_importedfile_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='cdn_enabled',
            field=models.BooleanField(default=False, verbose_name='CDN Enabled'),
        ),
    ]
