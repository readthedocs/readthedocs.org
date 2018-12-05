# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-31 11:25
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0008_add-project-relation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remoterepository',
            name='clone_url',
            field=models.URLField(blank=True, max_length=512, validators=[django.core.validators.URLValidator(schemes=['http', 'https', 'ssh', 'git', 'svn'])], verbose_name='Repository clone URL'),
        ),
        migrations.AlterField(
            model_name='remoterepository',
            name='ssh_url',
            field=models.URLField(blank=True, max_length=512, validators=[django.core.validators.URLValidator(schemes=['ssh'])], verbose_name='SSH URL'),
        ),
        migrations.AlterField(
            model_name='remoterepository',
            name='vcs',
            field=models.CharField(blank=True, choices=[('git', 'Git'), ('svn', 'Subversion'), ('hg', 'Mercurial'), ('bzr', 'Bazaar')], max_length=200, verbose_name='vcs'),
        ),
    ]
