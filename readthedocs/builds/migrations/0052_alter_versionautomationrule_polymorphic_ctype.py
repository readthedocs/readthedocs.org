# Generated by Django 4.2.4 on 2023-08-02 10:59
import django.db.models.deletion
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("builds", "0051_add_addons_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="versionautomationrule",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
    ]
