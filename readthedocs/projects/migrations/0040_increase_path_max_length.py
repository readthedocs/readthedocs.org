# Generated by Django 1.11.20 on 2019-02-23 15:05
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0039_update-doctype-helptext"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importedfile",
            name="path",
            field=models.CharField(max_length=4096, verbose_name="Path"),
        ),
    ]
