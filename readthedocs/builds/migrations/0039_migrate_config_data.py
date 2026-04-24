from django.db import migrations
from django.db.models import F
from django.db.models import JSONField
from django.db.models import Max
from django.db.models import Min
from django.db.models.functions import Cast
from django_safemigrate import Safe


def forwards_func(apps, schema_editor):
    """Copy build config to JSONField."""
    # Do migration in chunks, because prod Build table is a big boi.
    # We don't use `iterator()` here because `update()` will be quicker.
    Build = apps.get_model("builds", "Build")
    step = 10000
    build_pks = Build.objects.aggregate(min_pk=Min("id"), max_pk=Max("id"))
    build_min_pk, build_max_pk = (build_pks["min_pk"], build_pks["max_pk"])
    # Protection for tests, which have no build instances
    if not all([build_min_pk, build_max_pk]):
        return
    for first_pk in range(build_min_pk, build_max_pk, step):
        last_pk = first_pk + step
        build_update = (
            Build.objects.filter(
                pk__gte=first_pk,
                pk__lt=last_pk,
                _config_json__isnull=True,
            )
            .annotate(
                _config_in_json=Cast("_config", output_field=JSONField()),
            )
            .update(_config_json=F("_config_in_json"))
        )
        print(f"Migrated builds: first_pk={first_pk} last_pk={last_pk} updated={build_update}")


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("builds", "0038_add_new_jsonfields"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
