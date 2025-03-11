# Generated by Django 1.11.18 on 2019-02-04 16:49
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("projects", "0037_add_htmlfile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="python_interpreter",
            field=models.CharField(
                choices=[("python", "CPython 2.x"), ("python3", "CPython 3.x")],
                default="python3",
                help_text="The Python interpreter used to create the virtual environment.",
                max_length=20,
                verbose_name="Python Interpreter",
            ),
        ),
    ]
