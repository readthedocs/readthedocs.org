# -*- coding: utf-8 -*-
from django.db import migrations, models


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
