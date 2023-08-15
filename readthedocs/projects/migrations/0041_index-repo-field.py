# Generated by Django 1.11.20 on 2019-03-13 17:03
from django.db import migrations, models

import readthedocs.projects.validators


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0040_increase_path_max_length"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="repo",
            field=models.CharField(
                db_index=True,
                help_text="Hosted documentation repository URL",
                max_length=255,
                validators=[readthedocs.projects.validators.RepositoryURLValidator()],
                verbose_name="Repository URL",
            ),
        ),
    ]
