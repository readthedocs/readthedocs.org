# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_delete-url'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='use_virtualenv',
            new_name='install_project',
        ),
        migrations.AlterField(
            model_name='project',
            name='requirements_file',
            field=models.CharField(default=None, max_length=255, blank=True, help_text='A <a href="https://pip.pypa.io/en/latest/user_guide.html#requirements-files">pip requirements file</a> needed to build your documentation. Path from the root of your project.', null=True, verbose_name='Requirements file'),
        ),
        migrations.AlterField(
            model_name='project',
            name='single_version',
            field=models.BooleanField(default=False, help_text='A single version site has no translations and only your "latest" version, served at the root of the domain. Use this with caution, only turn it on if you will <b>never</b> have multiple versions of your docs.', verbose_name='Single version'),
        ),
    ]
