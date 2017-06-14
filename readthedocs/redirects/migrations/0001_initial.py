# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_add_importedfile_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='Redirect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('redirect_type', models.CharField(help_text='The type of redirect you wish to use.', max_length=255, verbose_name='Redirect Type', choices=[(b'prefix', 'Prefix Redirect'), (b'page', 'Page Redirect'), (b'exact', 'Exact Redirect'), (b'sphinx_html', 'Sphinx HTMLDir -> HTML'), (b'sphinx_htmldir', 'Sphinx HTML -> HTMLDir')])),
                ('from_url', models.CharField(help_text='Absolute path, excluding the domain. Example: <b>/docs/</b>  or <b>/install.html</b>', max_length=255, verbose_name='From URL', db_index=True, blank=True)),
                ('to_url', models.CharField(help_text='Absolute or relative url. Examples: <b>/tutorial/install.html</b>', max_length=255, verbose_name='To URL', db_index=True, blank=True)),
                ('http_status', models.SmallIntegerField(default=301, verbose_name='HTTP Status', choices=[(301, '301 - Permanent Redirect'), (302, '302 - Temporary Redirect')])),
                ('status', models.BooleanField(default=True, choices=[(True, 'Active'), (False, 'Inactive')])),
                ('create_dt', models.DateTimeField(auto_now_add=True)),
                ('update_dt', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(related_name='redirects', verbose_name='Project', to='projects.Project')),
            ],
            options={
                'ordering': ('-update_dt',),
                'verbose_name': 'redirect',
                'verbose_name_plural': 'redirects',
            },
        ),
    ]
