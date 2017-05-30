# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0013_add-container-limits'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='has_valid_clone',
            field=models.BooleanField(default=False, help_text='This project has been successfully cloned'),
        ),
        migrations.AddField(
            model_name='project',
            name='has_valid_webhook',
            field=models.BooleanField(default=False, help_text='This project has been build with a webhook'),
        ),
    ]
