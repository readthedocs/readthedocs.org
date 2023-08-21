# Generated by Django 4.2.4 on 2023-08-21 20:28

from django.db import migrations


def forwards_func(apps, schema_editor):
    """Migrate locked subscriptions to never_disable organizations."""
    Subscription = apps.get_model("subscriptions", "Subscription")
    locked_subscriptions = Subscription.objects.filter(locked=True).select_related(
        "organization"
    )
    for subscription in locked_subscriptions:
        subscription.organization.never_disable = True
        subscription.organization.save()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0012_add_organization_never_disable"),
        ("subscriptions", "0002_alter_planfeature_feature_type"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
