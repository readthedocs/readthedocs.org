# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0001_initial'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportedFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('slug', models.SlugField(verbose_name='Slug')),
                ('path', models.CharField(max_length=255, verbose_name='Path')),
                ('md5', models.CharField(max_length=255, verbose_name='MD5 checksum')),
                ('commit', models.CharField(max_length=255, verbose_name='Commit')),
                ('project', models.ForeignKey(related_name='imported_files', verbose_name='Project', to='projects.Project')),
                ('version', models.ForeignKey(related_name='imported_files', verbose_name='Version', to='builds.Version', null=True)),
            ],
        ),
    ]
