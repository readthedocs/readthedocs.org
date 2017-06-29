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
            name='DocumentComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('rating', models.IntegerField(default=0, verbose_name='Rating')),
                ('text', models.TextField(verbose_name='Text')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page', models.CharField(max_length=255, verbose_name='Path')),
                ('raw_source', models.TextField(verbose_name='Raw Source')),
                ('project', models.ForeignKey(related_name='nodes', verbose_name='Project', to='projects.Project', null=True)),
                ('version', models.ForeignKey(related_name='nodes', verbose_name='Version', to='builds.Version', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ModerationAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('decision', models.IntegerField(choices=[(0, b'No Decision'), (1, b'Publish'), (2, b'Hide')])),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('comment', models.ForeignKey(related_name='moderation_actions', to='comments.DocumentComment')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='ModerationActionManager',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='NodeSnapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Publication date')),
                ('hash', models.CharField(max_length=255, verbose_name='Hash')),
                ('commit', models.CharField(max_length=255)),
                ('node', models.ForeignKey(related_name='snapshots', to='comments.DocumentNode')),
            ],
            options={
                'get_latest_by': 'date',
            },
        ),
        migrations.AddField(
            model_name='documentcomment',
            name='node',
            field=models.ForeignKey(related_name='comments', to='comments.DocumentNode'),
        ),
        migrations.AddField(
            model_name='documentcomment',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='nodesnapshot',
            unique_together=set([('hash', 'node', 'commit')]),
        ),
    ]
