# -*- coding: utf-8 -*-
from django.db import migrations, models


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
