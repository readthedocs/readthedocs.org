# Generated by Django 2.2.16 on 2020-11-18 21:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("builds", "0030_add_automation_rule_matches"),
    ]

    operations = [
        migrations.AddField(
            model_name="build",
            name="version_name",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Version name"
            ),
        ),
        migrations.AddField(
            model_name="build",
            name="version_slug",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Version slug"
            ),
        ),
        migrations.AddField(
            model_name="build",
            name="version_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("branch", "Branch"),
                    ("tag", "Tag"),
                    ("external", "External"),
                    ("unknown", "Unknown"),
                ],
                max_length=32,
                null=True,
                verbose_name="Version type",
            ),
        ),
    ]
