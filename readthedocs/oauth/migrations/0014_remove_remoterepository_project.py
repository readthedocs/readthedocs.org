# Generated by Django 2.2.22 on 2021-06-14 15:42

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("oauth", "0013_create_new_table_for_remote_repository_normalization"),
        ("projects", "0077_remote_repository_data_migration"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="remoterepository",
            name="project",
        ),
    ]
