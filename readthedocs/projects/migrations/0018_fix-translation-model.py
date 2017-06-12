# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0017_add_domain_https'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='main_language_project',
            field=models.ForeignKey(related_name='translations', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Project', null=True),
        ),
    ]
