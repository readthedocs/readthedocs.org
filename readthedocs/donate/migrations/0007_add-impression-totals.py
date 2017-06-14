# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('donate', '0006_add-geo-data'),
    ]

    operations = [
        migrations.AddField(
            model_name='supporterpromo',
            name='sold_days',
            field=models.IntegerField(default=30, verbose_name='Sold Days'),
        ),
        migrations.AddField(
            model_name='supporterpromo',
            name='sold_impressions',
            field=models.IntegerField(default=1000, verbose_name='Sold Impressions'),
        ),
        migrations.AlterField(
            model_name='geofilter',
            name='countries',
            field=models.ManyToManyField(related_name='filters', to='donate.Country', blank=True),
        ),
    ]
