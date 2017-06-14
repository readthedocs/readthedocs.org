# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Supporter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('public', models.BooleanField(default=True, verbose_name='Public')),
                ('name', models.CharField(max_length=200, verbose_name='name', blank=True)),
                ('email', models.EmailField(max_length=200, verbose_name='Email', blank=True)),
                ('dollars', models.IntegerField(default=50, verbose_name='Amount', choices=[(5, b'$5'), (10, b'$10'), (25, b'$25'), (50, b'1 Hour ($50)'), (100, b'2 Hours ($100)'), (200, b'4 Hours ($200)'), (400, b'1 Day ($400)'), (800, b'2 Days ($800)'), (1200, b'3 Days ($1200)'), (1600, b'4 Days ($1600)'), (2000, b'5 Days ($2000)'), (4000, b'2 Weeks ($4000)'), (6000, b'3 Weeks ($6000)'), (8000, b'4 Weeks ($8000)')])),
                ('logo_url', models.URLField(max_length=255, null=True, verbose_name='Logo URL', blank=True)),
                ('site_url', models.URLField(max_length=255, null=True, verbose_name='Site URL', blank=True)),
                ('last_4_digits', models.CharField(max_length=4)),
                ('stripe_id', models.CharField(max_length=255)),
                ('subscribed', models.BooleanField(default=False)),
                ('user', models.ForeignKey(related_name='goldonce', verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SupporterPromo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('analytics_id', models.CharField(max_length=200, verbose_name='Analytics ID')),
                ('text', models.TextField(verbose_name='Text', blank=True)),
                ('link', models.URLField(max_length=255, null=True, verbose_name='Link URL', blank=True)),
                ('image', models.URLField(max_length=255, null=True, verbose_name='Image URL', blank=True)),
                ('display_type', models.CharField(default=b'doc', max_length=200, verbose_name='Display Type', choices=[(b'doc', b'Documentation Pages'), (b'site-footer', b'Site Footer'), (b'search', b'Search Pages')])),
                ('live', models.BooleanField(default=False, verbose_name='Live')),
            ],
        ),
    ]
