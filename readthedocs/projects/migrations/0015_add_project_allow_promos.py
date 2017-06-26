# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_add-state-tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='allow_promos',
            field=models.BooleanField(default=True, help_text='Allow sponsor advertisements on my project documentation', verbose_name='Sponsor advertisements'),
        ),
    ]
