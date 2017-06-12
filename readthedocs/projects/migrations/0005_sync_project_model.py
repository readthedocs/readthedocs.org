# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_add_project_container_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='documentation_type',
            field=models.CharField(default=b'sphinx', help_text='Type of documentation you are building. <a href="http://sphinx-doc.org/builders.html#sphinx.builders.html.DirectoryHTMLBuilder">More info</a>.', max_length=20, verbose_name='Documentation type', choices=[(b'auto', 'Automatically Choose'), (b'sphinx', 'Sphinx Html'), (b'mkdocs', 'Mkdocs (Markdown)'), (b'sphinx_htmldir', 'Sphinx HtmlDir'), (b'sphinx_singlehtml', 'Sphinx Single Page HTML')]),
        ),
        migrations.AlterField(
            model_name='project',
            name='single_version',
            field=models.BooleanField(default=False, help_text='A single version site has no translations and only your "latest" version, served at the root of the domain. Use this with caution, only turn it on if you will <b>never</b>have multiple versions of your docs.', verbose_name='Single version'),
        ),
        migrations.AlterField(
            model_name='project',
            name='use_virtualenv',
            field=models.BooleanField(default=False, help_text='Install your project inside a virtualenv using <code>setup.py install</code>', verbose_name='Install Project'),
        ),
    ]
