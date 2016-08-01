# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0016_build-queue-name'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='https',
            field=models.BooleanField(default=False, help_text='Use HTTPS', verbose_name='HTTPS', editable=False),
        ),
    ]
