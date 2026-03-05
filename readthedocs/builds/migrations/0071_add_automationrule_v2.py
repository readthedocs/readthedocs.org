# Generated manually

import django.db.models.deletion
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("builds", "0070_delete_build_old_config"),
        ("projects", "0126_remove_projectadmins"),
    ]

    operations = [
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
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, verbose_name="modified"),
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
                        help_text="List of version types this rule applies to (e.g., ['tag', 'branch', 'external']). Use ['any'] to match all version types.",
                        verbose_name="Version types",
                    ),
                ),
                (
                    "version_match_pattern",
                    models.CharField(
                        help_text="Regex pattern to match against the version name (e.g., '^release-.*')",
                        max_length=255,
                        verbose_name="Version match pattern",
                    ),
                ),
                (
                    "webhook_filter",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("label", "Label"),
                            ("commit_message", "Commit message"),
                            ("file_pattern", "File pattern"),
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
                    models.CharField(
                        blank=True,
                        help_text="Pattern to match against the webhook filter. For file_pattern, use comma-separated glob patterns (e.g., 'docs/*,*.rst'). For commit_message and label, use regex patterns.",
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
                    "action_arg",
                    models.CharField(
                        blank=True,
                        help_text="Optional argument for the action",
                        max_length=255,
                        null=True,
                        verbose_name="Action argument",
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
                        related_name="automation_rules_v2",
                        to="projects.project",
                        verbose_name="Project",
                    ),
                ),
            ],
            options={
                "verbose_name": "Automation rule",
                "verbose_name_plural": "Automation rules",
                "ordering": ("priority", "-modified", "-created"),
                "unique_together": {("project", "priority")},
            },
        ),
        migrations.CreateModel(
            name="AutomationRuleMatchV2",
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
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    models.DateTimeField(auto_now=True, verbose_name="modified"),
                ),
                (
                    "version_name",
                    models.CharField(max_length=255),
                ),
                (
                    "version_type",
                    models.CharField(
                        choices=[
                            ("branch", "Branch"),
                            ("tag", "Tag"),
                            ("external", "External"),
                            ("unknown", "Unknown"),
                        ],
                        max_length=32,
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
                        max_length=255,
                    ),
                ),
                (
                    "match_data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional data about what was matched (patterns, webhook data, etc.)",
                        null=True,
                        verbose_name="Match data",
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matches",
                        to="builds.automationrule",
                        verbose_name="Matched rule",
                    ),
                ),
            ],
            options={
                "verbose_name": "Automation rule match",
                "verbose_name_plural": "Automation rule matches",
                "ordering": ("-modified", "-created"),
            },
        ),
        migrations.AddIndex(
            model_name="automationrule",
            index=models.Index(
                fields=["project", "priority"],
                name="builds_auto_project_9b8b23_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="automationrule",
            index=models.Index(
                fields=["project", "enabled"],
                name="builds_auto_project_ab7c2f_idx",
            ),
        ),
    ]
