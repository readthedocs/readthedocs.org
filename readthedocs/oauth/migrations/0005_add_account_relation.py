# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('socialaccount', '0002_token_max_lengths'),
        ('oauth', '0004_drop_github_and_bitbucket_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='remoteorganization',
            name='account',
            field=models.ForeignKey(related_name='remote_organizations', verbose_name='Connected account', blank=True, to='socialaccount.SocialAccount', null=True),
        ),
        migrations.AddField(
            model_name='remoterepository',
            name='account',
            field=models.ForeignKey(related_name='remote_repositories', verbose_name='Connected account', blank=True, to='socialaccount.SocialAccount', null=True),
        ),
    ]
