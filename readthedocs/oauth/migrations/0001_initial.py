# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BitbucketProject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('full_name', models.CharField(unique=True, max_length=255, verbose_name='Full Name')),
                ('description', models.TextField(help_text='The reStructuredText description of the project', null=True, verbose_name='Description', blank=True)),
                ('vcs', models.CharField(max_length=200, verbose_name='vcs', blank=True)),
                ('git_url', models.CharField(max_length=200, verbose_name='Git URL', blank=True)),
                ('ssh_url', models.CharField(max_length=200, verbose_name='SSH URL', blank=True)),
                ('html_url', models.URLField(null=True, verbose_name='HTML URL', blank=True)),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('json', models.TextField(verbose_name=b'JSON')),
            ],
        ),
        migrations.CreateModel(
            name='BitbucketTeam',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('login', models.CharField(unique=True, max_length=255, verbose_name='Login')),
                ('email', models.EmailField(max_length=255, null=True, verbose_name='Email', blank=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name='Name', blank=True)),
                ('html_url', models.URLField(null=True, verbose_name='HTML URL', blank=True)),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('json', models.TextField(verbose_name=b'JSON')),
                ('users', models.ManyToManyField(related_name='bitbucket_organizations', verbose_name='Users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GithubOrganization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('login', models.CharField(unique=True, max_length=255, verbose_name='Login')),
                ('email', models.EmailField(max_length=255, null=True, verbose_name='Email', blank=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name='Name', blank=True)),
                ('html_url', models.URLField(null=True, verbose_name='HTML URL', blank=True)),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('json', models.TextField(verbose_name=b'JSON')),
                ('users', models.ManyToManyField(related_name='github_organizations', verbose_name='Users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GithubProject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('full_name', models.CharField(max_length=255, verbose_name='Full Name')),
                ('description', models.TextField(help_text='The reStructuredText description of the project', null=True, verbose_name='Description', blank=True)),
                ('git_url', models.CharField(max_length=200, verbose_name='Git URL', blank=True)),
                ('ssh_url', models.CharField(max_length=200, verbose_name='SSH URL', blank=True)),
                ('html_url', models.URLField(null=True, verbose_name='HTML URL', blank=True)),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('json', models.TextField(verbose_name=b'JSON')),
                ('organization', models.ForeignKey(related_name='projects', verbose_name='Organization', blank=True, to='oauth.GithubOrganization', null=True)),
                ('users', models.ManyToManyField(related_name='github_projects', verbose_name='Users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='bitbucketproject',
            name='organization',
            field=models.ForeignKey(related_name='projects', verbose_name='Organization', blank=True, to='oauth.BitbucketTeam', null=True),
        ),
        migrations.AddField(
            model_name='bitbucketproject',
            name='users',
            field=models.ManyToManyField(related_name='bitbucket_projects', verbose_name='Users', to=settings.AUTH_USER_MODEL),
        ),
    ]
