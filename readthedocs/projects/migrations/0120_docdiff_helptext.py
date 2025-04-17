# Generated by Django 4.2.10 on 2024-03-04 12:02

from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()
    dependencies = [
        ("projects", "0119_alter_addonsconfig_flyout_sorting_custom_pattern_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="addonsconfig",
            name="doc_diff_root_selector",
            field=models.CharField(
                blank=True,
                help_text="CSS selector for the main content of the page",
                max_length=128,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historicaladdonsconfig",
            name="doc_diff_root_selector",
            field=models.CharField(
                blank=True,
                help_text="CSS selector for the main content of the page",
                max_length=128,
                null=True,
            ),
        ),
    ]
