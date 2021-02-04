# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0033_dont_cascade_delete_builds'),
    ]

    operations = [
        migrations.AddField(
            model_name='environmentvariable',
            name='public',
            field=models.BooleanField(
                null=True,
                default=False,
                help_text='Expose this environment variable in PR builds?',
                verbose_name='Public',
            ),
        ),
    ]
