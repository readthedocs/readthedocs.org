# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_migrate_domain_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='domain',
            name='url',
        ),
    ]
