# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(related_name='profile', verbose_name='User', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
