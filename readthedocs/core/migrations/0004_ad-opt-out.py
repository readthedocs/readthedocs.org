# Generated by Django 1.9.12 on 2017-06-14 18:06
import annoying.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("core", "0003_add_banned_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="allow_ads",
            field=models.BooleanField(
                default=True,
                help_text="If unchecked, you will still see community ads.",
                verbose_name="See paid advertising",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="user",
            field=annoying.fields.AutoOneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="profile",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
    ]
