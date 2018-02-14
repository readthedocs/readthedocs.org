# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2018-02-14 07:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0002_add-webhook'),
    ]

    operations = [
        migrations.CreateModel(
            name='BitbucketWebhook',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('integrations.integration',),
        ),
        migrations.CreateModel(
            name='GenericAPIWebhook',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('integrations.integration',),
        ),
        migrations.CreateModel(
            name='GitHubWebhook',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('integrations.integration',),
        ),
        migrations.CreateModel(
            name='GitLabWebhook',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('integrations.integration',),
        ),
        migrations.AlterField(
            model_name='integration',
            name='integration_type',
            field=models.CharField(choices=[('github_webhook', 'GitHub incoming webhook'), ('bitbucket_webhook', 'Bitbucket incoming webhook'), ('gitlab_webhook', 'GitLab incoming webhook'), ('api_webhook', 'Generic API incoming webhook')], max_length=32, verbose_name='Integration type'),
        ),
    ]
