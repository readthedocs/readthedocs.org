from django.db import migrations
from django.db.models import Count
from django.db.models import F
from django.db.models.fields.json import KT
from django_safemigrate import Safe


BITBUCKET_PROVIDER_ID = "bitbucket_oauth2"
BATCH_SIZE = 1000


def forwards(apps, schema_editor):
    """
    Use the Bitbucket ``account_id`` as the uid of Bitbucket social accounts.

    allauth used to identify Bitbucket accounts by their username, which can change.
    It now uses the ``account_id``.

    Accounts without an ``account_id``, or sharing one with another account,
    are skipped and need to be handled manually.
    """
    SocialAccount = apps.get_model("socialaccount", "SocialAccount")
    accounts = SocialAccount.objects.filter(provider=BITBUCKET_PROVIDER_ID).annotate(
        account_id=KT("extra_data__account_id")
    )
    duplicated_account_ids = (
        accounts.filter(account_id__isnull=False)
        .values("account_id")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
        .values("account_id")
    )
    used_uids = SocialAccount.objects.filter(provider=BITBUCKET_PROVIDER_ID).values("uid")
    pks = list(
        accounts.filter(account_id__isnull=False)
        .exclude(uid=F("account_id"))
        .exclude(account_id__in=duplicated_account_ids)
        .exclude(account_id__in=used_uids)
        .values_list("pk", flat=True)
    )
    for i in range(0, len(pks), BATCH_SIZE):
        SocialAccount.objects.filter(pk__in=pks[i : i + BATCH_SIZE]).update(
            uid=KT("extra_data__account_id")
        )


class Migration(migrations.Migration):
    safe = Safe.after_deploy()

    dependencies = [
        ("oauth", "0019_fix_ssh_url_validators"),
        ("socialaccount", "0006_alter_socialaccount_extra_data"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
