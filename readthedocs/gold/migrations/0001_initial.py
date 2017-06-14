# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoldUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('level', models.CharField(default=b'supporter', max_length=20, verbose_name='Level', choices=[(b'v1-org-5', b'$5/mo'), (b'v1-org-10', b'$10/mo'), (b'v1-org-15', b'$15/mo'), (b'v1-org-20', b'$20/mo'), (b'v1-org-50', b'$50/mo'), (b'v1-org-100', b'$100/mo')])),
                ('last_4_digits', models.CharField(max_length=4)),
                ('stripe_id', models.CharField(max_length=255)),
                ('subscribed', models.BooleanField(default=False)),
                ('projects', models.ManyToManyField(related_name='gold_owners', verbose_name='Projects', to='projects.Project')),
                ('user', models.ForeignKey(related_name='gold', verbose_name='User', to=settings.AUTH_USER_MODEL, unique=True)),
            ],
        ),
    ]
