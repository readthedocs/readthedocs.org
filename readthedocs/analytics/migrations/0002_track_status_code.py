# Generated by Django 3.2.12 on 2022-03-29 17:51
import django.db.models.deletion
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("builds", "0041_track_task_id"),
        ("projects", "0087_use_booleanfield_null"),
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pageview",
            name="full_path",
            field=models.CharField(
                blank=True,
                help_text="Full path including the version and language parts.",
                max_length=4096,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="pageview",
            name="status",
            field=models.PositiveIntegerField(default=200, help_text="HTTP status code"),
        ),
        migrations.AlterField(
            model_name="pageview",
            name="path",
            field=models.CharField(help_text="Path relative to the version.", max_length=4096),
        ),
        migrations.AlterField(
            model_name="pageview",
            name="version",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="page_views",
                to="builds.version",
                verbose_name="Version",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="pageview",
            unique_together={("project", "version", "path", "date", "status")},
        ),
    ]
