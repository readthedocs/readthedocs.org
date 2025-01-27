# Generated by Django 1.9.13 on 2018-10-17 04:20
from django.db import migrations, models

import readthedocs.builds.version_slug


class Migration(migrations.Migration):
    dependencies = [
        ("builds", "0004_add-apiversion-proxy-model"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="versionalias",
            name="project",
        ),
        migrations.AlterField(
            model_name="build",
            name="error",
            field=models.TextField(blank=True, default="", verbose_name="Error"),
        ),
        migrations.AlterField(
            model_name="build",
            name="output",
            field=models.TextField(blank=True, default="", verbose_name="Output"),
        ),
        migrations.AlterField(
            model_name="build",
            name="state",
            field=models.CharField(
                choices=[
                    ("triggered", "Triggered"),
                    ("cloning", "Cloning"),
                    ("installing", "Installing"),
                    ("building", "Building"),
                    ("finished", "Finished"),
                ],
                default="finished",
                max_length=55,
                verbose_name="State",
            ),
        ),
        migrations.AlterField(
            model_name="build",
            name="type",
            field=models.CharField(
                choices=[
                    ("html", "HTML"),
                    ("pdf", "PDF"),
                    ("epub", "Epub"),
                    ("man", "Manpage"),
                    ("dash", "Dash"),
                ],
                default="html",
                max_length=55,
                verbose_name="Type",
            ),
        ),
        migrations.AlterField(
            model_name="version",
            name="privacy_level",
            field=models.CharField(
                choices=[
                    ("public", "Public"),
                    ("protected", "Protected"),
                    ("private", "Private"),
                ],
                default="public",
                help_text="Level of privacy for this Version.",
                max_length=20,
                verbose_name="Privacy Level",
            ),
        ),
        migrations.AlterField(
            model_name="version",
            name="slug",
            field=readthedocs.builds.version_slug.VersionSlugField(
                db_index=True,
                max_length=255,
                verbose_name="Slug",
            ),
        ),
        migrations.AlterField(
            model_name="version",
            name="type",
            field=models.CharField(
                choices=[("branch", "Branch"), ("tag", "Tag"), ("unknown", "Unknown")],
                default="unknown",
                max_length=20,
                verbose_name="Type",
            ),
        ),
        migrations.DeleteModel(
            name="VersionAlias",
        ),
    ]
