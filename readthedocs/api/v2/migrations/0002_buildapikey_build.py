from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("api_v2", "0001_initial"),
        # We add a nullable FK to Build; depend on the latest builds
        # migration at the time this one was written to keep the
        # dependency graph unambiguous.
        ("builds", "0072_remove_deprecated_build_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="buildapikey",
            name="build",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "Optional. When set, this API key is scoped to a specific "
                    "Build — writes are restricted to that Build (and its "
                    "Version, commands, notifications). When null, the key "
                    "retains project-wide scope (legacy behavior)."
                ),
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name="api_keys",
                to="builds.build",
            ),
        ),
    ]
