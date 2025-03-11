import django.db.models.deletion

# Generated by Django 2.2.22 on 2021-06-14 15:42
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("oauth", "0013_create_new_table_for_remote_repository_normalization"),
        ("projects", "0075_change_mkdocs_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="remote_repository",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="oauth.RemoteRepository",
            ),
        ),
    ]
