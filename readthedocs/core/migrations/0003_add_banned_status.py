# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_make_userprofile_user_a_onetoonefield'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='banned',
            field=models.BooleanField(default=False, verbose_name='Banned'),
        ),
    ]
