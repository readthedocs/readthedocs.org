# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0001_initial'),
        ('projects', '0002_add_importedfile_model'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page', models.CharField(max_length=255, verbose_name='Page')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('url', models.CharField(max_length=255, null=True, verbose_name='URL', blank=True)),
                ('project', models.ForeignKey(related_name='bookmarks', verbose_name='Project', to='projects.Project')),
                ('user', models.ForeignKey(related_name='bookmarks', verbose_name='User', to=settings.AUTH_USER_MODEL)),
                ('version', models.ForeignKey(related_name='bookmarks', verbose_name='Version', to='builds.Version')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='bookmark',
            unique_together=set([('user', 'project', 'version', 'page')]),
        ),
    ]
