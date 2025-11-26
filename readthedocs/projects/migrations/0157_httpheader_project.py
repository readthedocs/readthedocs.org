import django.db.models.deletion
from django.db import migrations, models


def forwards(apps, schema_editor):
    HTTPHeader = apps.get_model("projects", "HTTPHeader")
    for header in HTTPHeader.objects.all().select_related("domain"):
        if header.domain_id:
            header.project_id = header.domain.project_id
            header.save(update_fields=["project"])


def backwards(apps, schema_editor):
    # No safe way to restore the previous domain relationship.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0156_project_search_indexing_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="httpheader",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="http_headers",
                to="projects.project",
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="httpheader",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="http_headers",
                to="projects.project",
            ),
        ),
        migrations.RemoveField(
            model_name="httpheader",
            name="domain",
        ),
    ]
