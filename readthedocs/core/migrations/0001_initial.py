# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('whitelisted', models.BooleanField(default=False, verbose_name='Whitelisted')),
                ('homepage', models.CharField(max_length=100, verbose_name='Homepage', blank=True)),
                ('allow_email', models.BooleanField(default=True, help_text='Show your email on VCS contributions.', verbose_name='Allow email')),
                ('user', models.ForeignKey(related_name='profile', verbose_name='User', to=settings.AUTH_USER_MODEL, unique=True, on_delete=models.CASCADE)),
            ],
        ),
    ]
