from django.db import migrations
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()

    dependencies = [
        ("builds", "0071_alter_versionautomationrule_fk"),
        ("projects", "0163_automationrule_data_migration"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AutomationRuleMatch",
        ),
        migrations.DeleteModel(
            name="WebhookAutomationRule",
        ),
        migrations.DeleteModel(
            name="RegexAutomationRule",
        ),
        migrations.DeleteModel(
            name="VersionAutomationRule",
        ),
    ]
