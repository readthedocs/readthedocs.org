# Generated by Django 1.11.20 on 2019-04-25 23:04
import django.db.models.deletion
import django_extensions.db.fields
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0042_increase_env_variable_value_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("builds", "0006_add_config_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="VersionAutomationRule",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        help_text="A lower number (0) means a higher priority",
                        verbose_name="Rule priority",
                    ),
                ),
                (
                    "match_arg",
                    models.CharField(
                        help_text="Value used for the rule to match the version",
                        max_length=255,
                        verbose_name="Match argument",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("activate-version", "Activate version on match"),
                            ("set-default-version", "Set as default version on match"),
                        ],
                        max_length=32,
                        verbose_name="Action",
                    ),
                ),
                (
                    "action_arg",
                    models.CharField(
                        blank=True,
                        help_text="Value used for the action to perfom an operation",
                        max_length=255,
                        null=True,
                        verbose_name="Action argument",
                    ),
                ),
                (
                    "version_type",
                    models.CharField(
                        choices=[
                            ("branch", "Branch"),
                            ("tag", "Tag"),
                            ("unknown", "Unknown"),
                        ],
                        max_length=32,
                        verbose_name="Version type",
                    ),
                ),
                (
                    "polymorphic_ctype",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="polymorphic_builds.versionautomationrule_set+",
                        to="contenttypes.ContentType",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="automation_rules",
                        to="projects.Project",
                    ),
                ),
            ],
            options={
                "ordering": ("priority", "-modified", "-created"),
                # 'manager_inheritance_from_future': True,
            },
        ),
        migrations.CreateModel(
            name="RegexAutomationRule",
            fields=[],
            options={
                "proxy": True,
                # 'manager_inheritance_from_future': True,
                "indexes": [],
            },
            bases=("builds.versionautomationrule",),
        ),
        migrations.AlterUniqueTogether(
            name="versionautomationrule",
            unique_together=set([("project", "priority")]),
        ),
    ]
