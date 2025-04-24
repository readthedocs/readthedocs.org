from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("oauth", "0006_move_oauth_source"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="remoteorganization",
            name="source",
        ),
        migrations.RemoveField(
            model_name="remoterepository",
            name="source",
        ),
        migrations.AlterField(
            model_name="remoteorganization",
            name="slug",
            field=models.CharField(max_length=255, verbose_name="Slug"),
        ),
    ]
