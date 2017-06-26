# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
import readthedocs.builds.models


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuildCommandResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('command', models.TextField(verbose_name='Command')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('output', models.TextField(verbose_name='Command output', blank=True)),
                ('exit_code', models.IntegerField(verbose_name='Command exit code')),
                ('start_time', models.DateTimeField(verbose_name='Start time')),
                ('end_time', models.DateTimeField(verbose_name='End time')),
                ('build', models.ForeignKey(related_name='commands', verbose_name='Build', to='builds.Build')),
            ],
            options={
                'ordering': ['start_time'],
                'get_latest_by': 'start_time',
            },
            bases=(readthedocs.builds.models.BuildCommandResultMixin, models.Model),
        ),
    ]
