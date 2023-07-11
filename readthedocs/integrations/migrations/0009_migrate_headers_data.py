from django.db import migrations, models
from django.db.models import F
from django.db.models.functions import Cast


def forwards_func(apps, schema_editor):
    HttpExchange = apps.get_model('integrations', 'HttpExchange')
    (
        HttpExchange.objects
        .annotate(
            request_headers_in_json=Cast('request_headers', output_field=models.JSONField()),
            response_headers_in_json=Cast('response_headers', output_field=models.JSONField()),
        )
        .update(
            request_headers_json=F('request_headers_in_json'),
            response_headers_json=F('response_headers_in_json'),
        )
    )


    Integration = apps.get_model('integrations', 'Integration')
    (
        Integration.objects
        .annotate(
            provider_data_in_json=Cast('provider_data', output_field=models.JSONField()),
        )
        .update(
            provider_data_json=F('provider_data_in_json'),
        )
    )



class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0008_add_new_jsonfields'),
    ]

    operations = [
        migrations.RunPython(forwards_func)
    ]
