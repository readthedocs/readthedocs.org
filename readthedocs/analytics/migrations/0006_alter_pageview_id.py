# Generated by Django 3.2.15 on 2022-10-18 15:25
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("analytics", "0005_add_unique_constraint"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pageview",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
