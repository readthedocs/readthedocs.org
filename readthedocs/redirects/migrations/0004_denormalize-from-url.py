# Generated by Django 1.11.26 on 2020-03-14 14:15
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


def forward(apps, schema_editor):
    """Calculate new ``from_url_without_rest`` attribute."""
    Redirect = apps.get_model("redirects", "Redirect")

    queryset = Redirect.objects.filter(
        redirect_type="exact",
        from_url__endswith="$rest",
    )
    for redirect in queryset:
        redirect.from_url_without_rest = redirect.from_url.replace("$rest", "") or None
        redirect.save()


def backward(apps, schema_editor):
    # just no-op
    pass


class Migration(migrations.Migration):
    safe = Safe.after_deploy
    dependencies = [
        ("redirects", "0003_add_default_redirect_http_status_to_302"),
    ]

    operations = [
        migrations.AddField(
            model_name="redirect",
            name="from_url_without_rest",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Only for internal querying use",
                max_length=255,
                null=True,
            ),
        ),
        migrations.RunPython(forward, backward),
    ]
