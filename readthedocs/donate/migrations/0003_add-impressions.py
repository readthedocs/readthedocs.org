# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('donate', '0002_dollar-drop-choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupporterImpressions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(verbose_name='Date')),
                ('offers', models.IntegerField(default=0, verbose_name='Offer')),
                ('views', models.IntegerField(default=0, verbose_name='View')),
                ('clicks', models.IntegerField(default=0, verbose_name='Clicks')),
                ('promo', models.ForeignKey(related_name='impressions', blank=True, to='donate.SupporterPromo', null=True)),
            ],
            options={
                'ordering': ('-date',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='supporterimpressions',
            unique_together=set([('promo', 'date')]),
        ),
    ]
