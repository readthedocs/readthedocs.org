# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0003_move_github'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bitbucketproject',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='bitbucketproject',
            name='users',
        ),
        migrations.RemoveField(
            model_name='bitbucketteam',
            name='users',
        ),
        migrations.RemoveField(
            model_name='githuborganization',
            name='users',
        ),
        migrations.RemoveField(
            model_name='githubproject',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='githubproject',
            name='users',
        ),
        migrations.DeleteModel(
            name='BitbucketProject',
        ),
        migrations.DeleteModel(
            name='BitbucketTeam',
        ),
        migrations.DeleteModel(
            name='GithubOrganization',
        ),
        migrations.DeleteModel(
            name='GithubProject',
        ),
    ]
