# Generated by Django 4.2.17 on 2025-01-27 18:32

import django.core.validators
from django.db import migrations, models
from django_safemigrate import Safe


class Migration(migrations.Migration):

    safe = Safe.after_deploy

    dependencies = [
        ("builds", "0059_add_version_date_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="version",
            name="slug",
            field=models.CharField(
                db_index=True,
                help_text="A unique identifier used in the URL and links for this version. It can contain lowercase letters, numbers, dots, dashes or underscores. It must start with a lowercase letter or a number.",
                max_length=255,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Enter a valid slug consisting of lowercase letters, numbers, dots, dashes or underscores. It must start with a letter or a number.",
                        regex="^(?:[a-z0-9a-z][-._a-z0-9a-z]*?)$",
                    )
                ],
                verbose_name="Slug",
            ),
        ),
    ]
