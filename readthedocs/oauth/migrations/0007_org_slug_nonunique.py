# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0006_move_oauth_source'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='remoteorganization',
            name='source',
        ),
        migrations.RemoveField(
            model_name='remoterepository',
            name='source',
        ),
        migrations.AlterField(
            model_name='remoteorganization',
            name='slug',
            field=models.CharField(max_length=255, verbose_name='Slug'),
        ),
    ]
