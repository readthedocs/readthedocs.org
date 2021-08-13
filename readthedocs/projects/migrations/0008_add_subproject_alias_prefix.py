# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_migrate_canonical_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectrelationship',
            name='alias',
            field=models.CharField(max_length=255, null=True, verbose_name='Alias', blank=True),
        ),
    ]
