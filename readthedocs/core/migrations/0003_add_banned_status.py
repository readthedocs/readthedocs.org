from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("core", "0002_make_userprofile_user_a_onetoonefield"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="banned",
            field=models.BooleanField(default=False, verbose_name="Banned"),
        ),
    ]
