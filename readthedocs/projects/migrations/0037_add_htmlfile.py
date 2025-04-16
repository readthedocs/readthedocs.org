# Generated by Django 1.11.18 on 2019-01-22 19:13
from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0036_remove-auto-doctype"),
    ]

    operations = [
        migrations.CreateModel(
            name="HTMLFile",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
            },
            bases=("projects.importedfile",),
        ),
    ]
