import django.db.models.deletion
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    # Nothing runs against the database: the model is renamed in Django's
    # state only and keeps pointing at the ``v2_buildapikey`` table.
    safe = Safe.always()

    dependencies = [
        ("projects", "0169_external_builds_enabled_default_true"),
        ("v2", "0002_project_api_key_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel(
                    old_name="BuildAPIKey",
                    new_name="ProjectAPIKey",
                ),
                migrations.AlterModelTable(
                    name="projectapikey",
                    table="v2_buildapikey",
                ),
                migrations.AlterModelOptions(
                    name="projectapikey",
                    options={
                        "ordering": ("-created",),
                        "verbose_name": "Project API key",
                        "verbose_name_plural": "Project API keys",
                    },
                ),
                migrations.AlterField(
                    model_name="projectapikey",
                    name="project",
                    field=models.ForeignKey(
                        help_text="Project that this API key grants access to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_keys",
                        to="projects.project",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
