# Generated by Django 3.2.15 on 2022-10-18 15:43
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("search", "0004_make_total_results_not_null"),
    ]

    operations = [
        migrations.AlterField(
            model_name="searchquery",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
