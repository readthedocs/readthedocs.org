# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
import django.contrib.sites.models

import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_add_subproject_alias_prefix'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='domain',
            options={'ordering': ('-canonical', '-machine', 'domain')},
        ),
        migrations.AddField(
            model_name='domain',
            name='domain',
            field=models.CharField(null=True, max_length=255, verbose_name='Domain', validators=[django.contrib.sites.models._simple_domain_name_validator]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='domain',
            name='canonical',
            field=models.BooleanField(default=False, help_text='This Domain is the primary one where the documentation is served from.'),
        ),
        migrations.AlterField(
            model_name='domain',
            name='cname',
            field=models.BooleanField(default=False, help_text='This Domain is a CNAME for the project'),
        ),
        migrations.AlterField(
            model_name='domain',
            name='machine',
            field=models.BooleanField(default=False, help_text='This Domain was auto-created'),
        ),
        migrations.AlterField(
            model_name='domain',
            name='url',
            field=models.URLField(unique=True, verbose_name='domain'),
        ),
    ]
