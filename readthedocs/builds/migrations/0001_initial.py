# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
import readthedocs.builds.version_slug
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
        ('taggit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Build',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'html', max_length=55, verbose_name='Type', choices=[(b'html', 'HTML'), (b'pdf', 'PDF'), (b'epub', 'Epub'), (b'man', 'Manpage'), (b'dash', 'Dash')])),
                ('state', models.CharField(default=b'finished', max_length=55, verbose_name='State', choices=[(b'triggered', 'Triggered'), (b'cloning', 'Cloning'), (b'installing', 'Installing'), (b'building', 'Building'), (b'finished', 'Finished')])),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('success', models.BooleanField(default=True, verbose_name='Success')),
                ('setup', models.TextField(null=True, verbose_name='Setup', blank=True)),
                ('setup_error', models.TextField(null=True, verbose_name='Setup error', blank=True)),
                ('output', models.TextField(default=b'', verbose_name='Output', blank=True)),
                ('error', models.TextField(default=b'', verbose_name='Error', blank=True)),
                ('exit_code', models.IntegerField(null=True, verbose_name='Exit code', blank=True)),
                ('commit', models.CharField(max_length=255, null=True, verbose_name='Commit', blank=True)),
                ('length', models.IntegerField(null=True, verbose_name='Build Length', blank=True)),
                ('builder', models.CharField(max_length=255, null=True, verbose_name='Builder', blank=True)),
                ('project', models.ForeignKey(related_name='builds', verbose_name='Project', to='projects.Project')),
            ],
            options={
                'ordering': ['-date'],
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'unknown', max_length=20, verbose_name='Type', choices=[(b'branch', 'Branch'), (b'tag', 'Tag'), (b'unknown', 'Unknown')])),
                ('identifier', models.CharField(max_length=255, verbose_name='Identifier')),
                ('verbose_name', models.CharField(max_length=255, verbose_name='Verbose Name')),
                ('slug', readthedocs.builds.version_slug.VersionSlugField(populate_from=b'verbose_name', max_length=255, verbose_name='Slug', db_index=True)),
                ('supported', models.BooleanField(default=True, verbose_name='Supported')),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('built', models.BooleanField(default=False, verbose_name='Built')),
                ('uploaded', models.BooleanField(default=False, verbose_name='Uploaded')),
                ('privacy_level', models.CharField(default=b'public', help_text='Level of privacy for this Version.', max_length=20, verbose_name='Privacy Level', choices=[(b'public', 'Public'), (b'protected', 'Protected'), (b'private', 'Private')])),
                ('machine', models.BooleanField(default=False, verbose_name='Machine Created')),
                ('project', models.ForeignKey(related_name='versions', verbose_name='Project', to='projects.Project')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'ordering': ['-verbose_name'],
                'permissions': (('view_version', 'View Version'),),
            },
        ),
        migrations.CreateModel(
            name='VersionAlias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_slug', models.CharField(default=b'', max_length=255, verbose_name='From slug')),
                ('to_slug', models.CharField(default=b'', max_length=255, verbose_name='To slug', blank=True)),
                ('largest', models.BooleanField(default=False, verbose_name='Largest')),
                ('project', models.ForeignKey(related_name='aliases', verbose_name='Project', to='projects.Project')),
            ],
        ),
        migrations.AddField(
            model_name='build',
            name='version',
            field=models.ForeignKey(related_name='builds', verbose_name='Version', to='builds.Version', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='version',
            unique_together=set([('project', 'slug')]),
        ),
        migrations.AlterIndexTogether(
            name='build',
            index_together=set([('version', 'state', 'type')]),
        ),
    ]
