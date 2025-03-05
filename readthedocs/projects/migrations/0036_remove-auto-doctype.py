# Generated by Django 1.11.16 on 2018-12-17 17:32
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


def migrate_auto_doctype(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(documentation_type="auto").update(
        documentation_type="sphinx",
    )


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("projects", "0035_container_time_limit_as_integer"),
    ]

    operations = [
        migrations.RunPython(migrate_auto_doctype),
        migrations.AlterField(
            model_name="project",
            name="documentation_type",
            field=models.CharField(
                choices=[
                    ("sphinx", "Sphinx Html"),
                    ("mkdocs", "Mkdocs (Markdown)"),
                    ("sphinx_htmldir", "Sphinx HtmlDir"),
                    ("sphinx_singlehtml", "Sphinx Single Page HTML"),
                ],
                default="sphinx",
                help_text='Type of documentation you are building. <a href="http://www.sphinx-doc.org/en/stable/builders.html#sphinx.builders.html.DirectoryHTMLBuilder">More info</a>.',
                max_length=20,
                verbose_name="Documentation type",
            ),
        ),
    ]
