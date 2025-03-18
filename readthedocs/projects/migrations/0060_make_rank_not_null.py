# Generated by Django 2.2.12 on 2020-07-07 23:35
import django.core.validators
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("projects", "0059_migrate_null_rank"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importedfile",
            name="rank",
            field=models.IntegerField(
                default=0,
                validators=[
                    django.core.validators.MinValueValidator(-10),
                    django.core.validators.MaxValueValidator(10),
                ],
                verbose_name="Page search rank",
            ),
        ),
    ]
