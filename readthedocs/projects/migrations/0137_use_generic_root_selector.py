# Generated by Django 4.2.16 on 2024-11-20 12:35

from django.db import migrations, models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy

    dependencies = [
        ('projects', '0136_addons_customscript_notnull'),
    ]

    operations = [
        migrations.AddField(
            model_name='addonsconfig',
            name='options_root_selector',
            field=models.CharField(blank=True, help_text='CSS selector for the main content of the page. Leave it blank for auto-detect.', max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='historicaladdonsconfig',
            name='options_root_selector',
            field=models.CharField(blank=True, help_text='CSS selector for the main content of the page. Leave it blank for auto-detect.', max_length=128, null=True),
        ),
    ]