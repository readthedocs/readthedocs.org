import importlib

from allauth.socialaccount.models import SocialAccount
from django.apps import apps
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get


migration = importlib.import_module(
    "readthedocs.oauth.migrations.0020_bitbucket_socialaccount_uid"
)


class BitbucketSocialAccountUidMigrationTest(TestCase):
    def _account(self, uid, extra_data, provider="bitbucket_oauth2"):
        return get(
            SocialAccount,
            provider=provider,
            uid=uid,
            extra_data=extra_data,
            user=get(User),
        )

    def test_migrate_uids(self):
        migrated = self._account("username", {"account_id": "557058:abc", "username": "username"})
        already_migrated = self._account("557058:def", {"account_id": "557058:def"})
        missing = self._account("missing", {"username": "missing"})
        null = self._account("null", {"account_id": None})
        dupe_1 = self._account("dupe-1", {"account_id": "557058:dupe"})
        dupe_2 = self._account("dupe-2", {"account_id": "557058:dupe"})
        # The account_id is already the uid of another account.
        taken = self._account("taken", {"account_id": "557058:def"})
        github = self._account("1234", {"account_id": "557058:gh"}, provider="github")

        migration.forwards(apps, None)

        expected = {
            migrated: "557058:abc",
            already_migrated: "557058:def",
            missing: "missing",
            null: "null",
            dupe_1: "dupe-1",
            dupe_2: "dupe-2",
            taken: "taken",
            github: "1234",
        }
        for account, uid in expected.items():
            account.refresh_from_db()
            assert account.uid == uid
