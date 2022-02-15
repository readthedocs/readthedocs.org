from django.db import migrations, models
from django.db.models import F
from django.db.models.functions import Cast


def forwards_func(apps, schema_editor):
    Build = apps.get_model('builds', 'Build')
    (
        Build.objects
        .annotate(_config_in_json=Cast('_config', output_field=models.JSONField()))
        # Copy `_config` JSONField (text) into `_config_json` (jsonb)
        .update(_config_json=F('_config_in_json'))
    )


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0038_add_new_jsonfields'),
    ]

    operations = [
        migrations.RunPython(forwards_func)
    ]
