from django.conf import settings
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="user",
            field=models.OneToOneField(
                related_name="profile",
                verbose_name="User",
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
            ),
        ),
    ]
