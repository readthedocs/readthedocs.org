# Generated by Django 4.2.5 on 2023-11-22 16:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("builds", "0055_alter_versionautomationrule_priority"),
    ]

    operations = [
        migrations.AlterField(
            model_name="versionautomationrule",
            name="priority",
            field=models.PositiveIntegerField(
                default=0,
                help_text="A lower number (0) means a higher priority",
                verbose_name="Rule priority",
            ),
        ),
    ]
