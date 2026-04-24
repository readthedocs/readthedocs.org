import django.db.models.deletion
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0017_add_domain_https"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="main_language_project",
            field=models.ForeignKey(
                related_name="translations",
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                to="projects.Project",
                null=True,
            ),
        ),
    ]
