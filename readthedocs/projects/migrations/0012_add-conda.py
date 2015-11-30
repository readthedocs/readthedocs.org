# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_delete-url'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='use_conda',
            field=models.BooleanField(default=False, help_text='Useful for Scientific Python and others with C dependencies.', verbose_name='Use Conda for build environment'),
        ),
    ]
