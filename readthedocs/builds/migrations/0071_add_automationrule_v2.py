# Generated manually

import django.db.models.deletion
import django_extensions
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


def forward_migrate_data(apps, schema_editor):
    RegexAutomationRule = apps.get_model("builds", "RegexAutomationRule")
    AutomationRule = apps.get_model("builds", "AutomationRule")

    for rule in RegexAutomationRule.objects.iterator():
        AutomationRule.objects.create(
            # Keep the same date for the migrated rules.
            created=rule.created,
            modified=rule.modified,
            project=rule.project,
            priority=rule.priority,
            description=rule.description,
            version_types=[rule.version_type],
            version_match_pattern=rule.match_arg,
            # ``predefined_match_arg`` could be:
            # - semver-versions
            # - all-versions
            version_predefined_match_pattern=rule.predefined_match_arg,
            webhook_filter=rule.webhook_filter,
            webhook_match_pattern=rule.webhook_match_pattern,
            action=rule.action,
            enabled=True,
        )


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("builds", "0070_delete_build_old_config"),
        ("projects", "0158_add_search_subproject_filter_option"),
    ]

    operations = [
        migrations.AlterField(
            model_name="versionautomationrule",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="version_automation_rules",
                to="projects.project",
            ),
        ),
        migrations.CreateModel(
            name="AutomationRule",
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
                    models.PositiveIntegerField(
                        default=0,
                        help_text="A lower number (0) means a higher priority",
                        verbose_name="Rule priority",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "version_types",
                    models.JSONField(
                        default=list,
                        help_text="List of version types this rule applies to (e.g., ['tag', 'branch', 'external']).",
                        verbose_name="Version types",
                    ),
                ),
                (
                    "version_predefined_match_pattern",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("all-versions", "Any version"),
                            ("semver-versions", "SemVer versions"),
                            (None, "Custom match"),
                        ],
                        help_text="Predefined pattern to match against the version name (e.g., 'semver-versions')",
                        max_length=255,
                        null=True,
                        verbose_name="Version predefined match pattern",
                    ),
                ),
                (
                    "version_match_pattern",
                    models.CharField(
                        blank=True,
                        help_text="Regex pattern to match against the version name (e.g., '^release-.*')",
                        max_length=255,
                        null=True,
                        verbose_name="Version match pattern",
                    ),
                ),
                (
                    "webhook_filter",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("label", "Label"),
                            ("commit-message", "Commit message"),
                            ("file-pattern", "File pattern"),
                        ],
                        default=None,
                        help_text="Type of webhook filter to apply. When None, version management actions are supported. When set, only 'trigger build' action is supported.",
                        max_length=32,
                        null=True,
                        verbose_name="Webhook filter",
                    ),
                ),
                (
                    "webhook_match_pattern",
                    models.JSONField(
                        blank=True,
                        help_text="Pattern to match against the webhook filter. For file_pattern, one fnmatch patterns For commit_message and label, use only regex patterns. You can use one pattern per line.",
                        max_length=1024,
                        null=True,
                        verbose_name="Webhook match pattern",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("activate-version", "Activate version"),
                            ("hide-version", "Hide version"),
                            ("make-version-public", "Make version public"),
                            ("make-version-private", "Make version private"),
                            ("set-default-version", "Set version as default"),
                            ("delete-version", "Delete version"),
                            ("trigger-build", "Trigger build for version"),
                        ],
                        help_text="Action to apply when the rule matches",
                        max_length=32,
                        verbose_name="Action",
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Whether this rule is enabled",
                        verbose_name="Enabled",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="automation_rules",
                        to="projects.project",
                        verbose_name="Project",
                    ),
                ),
            ],
            options={
                "verbose_name": "Automation rule",
                "verbose_name_plural": "Automation rules",
                "ordering": ("priority", "-modified", "-created"),
            },
        ),
        migrations.AlterField(
            model_name="automationrulematch",
            name="rule",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="matches",
                to="builds.automationrule",
                verbose_name="Matched rule",
            ),
        ),
        migrations.RunPython(
            forward_migrate_data,
            migrations.RunPython.noop,
        ),
    ]
