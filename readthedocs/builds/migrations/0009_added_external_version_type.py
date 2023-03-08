# Generated by Django 1.11.21 on 2019-07-04 13:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0008_remove-version-tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='version',
            name='type',
            field=models.CharField(choices=[('branch', 'Branch'), ('tag', 'Tag'), ('external', 'External'), ('unknown', 'Unknown')], default='unknown', max_length=20, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='versionautomationrule',
            name='version_type',
            field=models.CharField(choices=[('branch', 'Branch'), ('tag', 'Tag'), ('external', 'External'), ('unknown', 'Unknown')], max_length=32, verbose_name='Version type'),
        ),
    ]
