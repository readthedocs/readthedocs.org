from django.db import migrations, models


class Migration(migrations.Migration):
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
