# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_project_cdn_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='container_image',
            field=models.CharField(max_length=64, null=True, verbose_name='Alternative container image', blank=True),
        ),
    ]
