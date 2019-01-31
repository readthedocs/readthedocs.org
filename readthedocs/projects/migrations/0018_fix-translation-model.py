# -*- coding: utf-8 -*-
import django.db.models.deletion
from django.db import migrations, models


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
