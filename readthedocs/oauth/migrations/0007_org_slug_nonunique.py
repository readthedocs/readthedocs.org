# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0006_move_oauth_source'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='remoteorganization',
            name='source',
        ),
        migrations.RemoveField(
            model_name='remoterepository',
            name='source',
        ),
        migrations.AlterField(
            model_name='remoteorganization',
            name='slug',
            field=models.CharField(max_length=255, verbose_name='Slug'),
        ),
    ]
