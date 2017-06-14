# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oauth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteOrganization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('slug', models.CharField(unique=True, max_length=255, verbose_name='Slug')),
                ('name', models.CharField(max_length=255, null=True, verbose_name='Name', blank=True)),
                ('email', models.EmailField(max_length=255, null=True, verbose_name='Email', blank=True)),
                ('avatar_url', models.URLField(null=True, verbose_name='Avatar image URL', blank=True)),
                ('url', models.URLField(null=True, verbose_name='URL to organization page', blank=True)),
                ('source', models.CharField(max_length=16, verbose_name='Repository source', choices=[(b'github', 'GitHub'), (b'bitbucket', 'Bitbucket')])),
                ('json', models.TextField(verbose_name='Serialized API response')),
                ('users', models.ManyToManyField(related_name='oauth_organizations', verbose_name='Users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RemoteRepository',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('full_name', models.CharField(max_length=255, verbose_name='Full Name')),
                ('description', models.TextField(help_text='Description of the project', null=True, verbose_name='Description', blank=True)),
                ('avatar_url', models.URLField(null=True, verbose_name='Owner avatar image URL', blank=True)),
                ('ssh_url', models.URLField(blank=True, max_length=512, verbose_name='SSH URL', validators=[django.core.validators.URLValidator(schemes=[b'ssh'])])),
                ('clone_url', models.URLField(blank=True, max_length=512, verbose_name='Repository clone URL', validators=[django.core.validators.URLValidator(schemes=[b'http', b'https', b'ssh', b'git', b'svn'])])),
                ('html_url', models.URLField(null=True, verbose_name='HTML URL', blank=True)),
                ('private', models.BooleanField(default=False, verbose_name='Private repository')),
                ('admin', models.BooleanField(default=False, verbose_name='Has admin privilege')),
                ('vcs', models.CharField(blank=True, max_length=200, verbose_name='vcs', choices=[(b'git', 'Git'), (b'svn', 'Subversion'), (b'hg', 'Mercurial'), (b'bzr', 'Bazaar')])),
                ('source', models.CharField(max_length=16, verbose_name='Repository source', choices=[(b'github', 'GitHub'), (b'bitbucket', 'Bitbucket')])),
                ('json', models.TextField(verbose_name='Serialized API response')),
                ('organization', models.ForeignKey(related_name='repositories', verbose_name='Organization', blank=True, to='oauth.RemoteOrganization', null=True)),
                ('users', models.ManyToManyField(related_name='oauth_repositories', verbose_name='Users', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['organization__name', 'name'],
                'verbose_name_plural': 'remote repositories',
            },
        ),
    ]
