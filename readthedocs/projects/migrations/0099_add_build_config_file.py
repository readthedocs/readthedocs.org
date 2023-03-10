# Generated by Django 3.2.18 on 2023-03-10 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0098_pdf_epub_opt_in"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalproject",
            name="build_config_file",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="<strong>Warning: experimental feature</strong>. Custom path from repository root to a build configuration file, ex. <code>subproject/docs/.readthedocs.yaml</code>. Leave blank for default value (<code>.readthedocs.yaml</code>).",
                max_length=1024,
                null=True,
                verbose_name="Build configuration file",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="build_config_file",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="<strong>Warning: experimental feature</strong>. Custom path from repository root to a build configuration file, ex. <code>subproject/docs/.readthedocs.yaml</code>. Leave blank for default value (<code>.readthedocs.yaml</code>).",
                max_length=1024,
                null=True,
                verbose_name="Build configuration file",
            ),
        ),
    ]
