# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('donate', '0004_rebase-impressions-on-base'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', django_countries.fields.CountryField(unique=True, max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='GeoFilter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filter_type', models.CharField(default=b'', max_length=20, verbose_name='Filter Type', choices=[(b'exclude', b'Exclude'), (b'include', b'Include')])),
                ('countries', models.ManyToManyField(related_name='filters', null=True, to='donate.Country', blank=True)),
                ('promo', models.ForeignKey(related_name='geo_filters', blank=True, to='donate.SupporterPromo', null=True)),
            ],
        ),
    ]
