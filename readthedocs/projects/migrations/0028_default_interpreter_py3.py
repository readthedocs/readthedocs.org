# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-09-06 07:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0027_remove_json_with_html_feature'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='python_interpreter',
            field=models.CharField(choices=[('python', 'CPython 2.x'), ('python3', 'CPython 3.x')], default='python3', help_text='The Python interpreter used to create the virtual environment.', max_length=20, verbose_name='Python Interpreter'),
        ),
    ]
