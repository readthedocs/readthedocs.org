# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


def forwards_remove_content_types(apps, schema_editor):
    db = schema_editor.connection.alias
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.using(db).filter(
        app_label='oauth',
        model__in=['githubproject', 'githuborganization',
                   'bitbucketproject', 'bitbucketteam']
    ).delete()


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
        migrations.RunPython(forwards_remove_content_types),
    ]
