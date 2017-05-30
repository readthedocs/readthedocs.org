# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


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
