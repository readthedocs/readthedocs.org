from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("projects", "0070_make_md5_field_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="environmentvariable",
            name="public",
            field=models.BooleanField(
                null=True,
                default=False,
                help_text="Expose this environment variable in PR builds?",
                verbose_name="Public",
            ),
        ),
    ]
