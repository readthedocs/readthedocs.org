# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_add-state-tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='allow_promos',
            field=models.BooleanField(default=True, help_text='Allow sponsor advertisements on my project documentation', verbose_name='Sponsor advertisements'),
        ),
    ]
