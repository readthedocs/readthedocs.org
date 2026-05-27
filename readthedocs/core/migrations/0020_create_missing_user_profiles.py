from django.conf import settings
from django.db import migrations
from django_safemigrate import Safe


def forwards_create_missing_profiles(apps, schema_editor):
    """
    Create a profile for users that don't have one yet.

    The ``user`` field used to be an ``AutoOneToOneField`` that created the
    profile lazily on access, so existing users may not have a profile row.
    """
    User = apps.get_model(settings.AUTH_USER_MODEL)
    UserProfile = apps.get_model("core", "UserProfile")

    users_without_profile = User.objects.filter(profile__isnull=True)
    UserProfile.objects.bulk_create(
        (UserProfile(user=user) for user in users_without_profile.iterator()),
        batch_size=500,
    )


class Migration(migrations.Migration):
    safe = Safe.before_deploy()

    dependencies = [
        ("core", "0019_alter_userprofile_user"),
    ]

    operations = [
        migrations.RunPython(
            forwards_create_missing_profiles,
            migrations.RunPython.noop,
        ),
    ]
