# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0016_build-queue-name'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='https',
            field=models.BooleanField(default=False, help_text='SSL is enabled for this domain', verbose_name='Use HTTPS'),
        ),
    ]
