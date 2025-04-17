# Generated by Django 4.2.17 on 2025-02-18 21:38

from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("core", "0016_update_dj_simple_history"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicaluser",
            name="extra_history_user_id",
            field=models.IntegerField(blank=True, null=True, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="historicaluser",
            name="extra_history_user_username",
            field=models.CharField(max_length=150, null=True, verbose_name="username"),
        ),
        migrations.AlterField(
            model_name="historicaluserprofile",
            name="extra_history_user_id",
            field=models.IntegerField(blank=True, null=True, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="historicaluserprofile",
            name="extra_history_user_username",
            field=models.CharField(max_length=150, null=True, verbose_name="username"),
        ),
    ]
