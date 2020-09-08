from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization, Team, TeamInvite


class InviteTests(TestCase):

    def setUp(self):
        self.organization = get(Organization)
        self.team = get(Team, organization=self.organization)

    def test_invite(self):
        invite = get(
            TeamInvite, organization=self.organization,
            team=self.team,
        )
        self.assertIsNotNone(invite.hash)
        self.assertEqual(len(invite.hash), 20)
        self.assertRegex(invite.hash, r'^\w{20}$')

        # Changing fields doesn't alter hash
        old_hash = invite.hash
        invite.save()
        self.assertEqual(old_hash, invite.hash)
        invite.count += 1
        invite.save()
        self.assertEqual(old_hash, invite.hash)

        # Changing keyed fields doesn't
        invite.email = 'foo+' + invite.email
        invite.save()
        self.assertNotEqual(old_hash, invite.hash)

    def test_duplicate_invite_unique(self):
        """Regression against duplicated hashes."""
        invite_a = get(
            TeamInvite, organization=self.organization,
            team=self.team,
        )
        invite_b = get(
            TeamInvite, organization=self.organization,
            team=self.team,
        )
        self.assertNotEqual(invite_a.hash, invite_b.hash)
