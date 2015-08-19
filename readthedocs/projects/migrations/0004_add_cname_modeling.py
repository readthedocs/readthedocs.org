# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_project_cdn_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(unique=True, verbose_name='Name')),
                ('canonical', models.BooleanField(default=False, help_text='This URL is where the documentation is served from.', verbose_name='Canonical')),
                ('active', models.BooleanField(default=False, help_text='This is an active domain for this project.', verbose_name='Default')),
            ],
        ),
        migrations.AlterField(
            model_name='project',
            name='documentation_type',
            field=models.CharField(default=b'sphinx', help_text='Type of documentation you are building. <a href="http://sphinx-doc.org/builders.html#sphinx.builders.html.DirectoryHTMLBuilder">More info</a>.', max_length=20, verbose_name='Documentation type', choices=[(b'auto', 'Automatically Choose'), (b'sphinx', 'Sphinx Html'), (b'mkdocs', 'Mkdocs (Markdown)'), (b'sphinx_htmldir', 'Sphinx HtmlDir'), (b'sphinx_singlehtml', 'Sphinx Single Page HTML')]),
        ),
        migrations.AddField(
            model_name='domain',
            name='project',
            field=models.ForeignKey(related_name='domains', to='projects.Project'),
        ),
    ]
