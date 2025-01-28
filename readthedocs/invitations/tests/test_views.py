from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.audit.models import AuditLog
from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization, Team, TeamInvite
from readthedocs.projects.models import Project


class TestViews(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.organization = get(
            Organization, owners=[self.user], projects=[self.project]
        )
        self.team = get(Team, organization=self.organization)
        self.another_user = get(User)
        self.email = "test@example.com"
        self.invitation, _ = Invitation.objects.invite(
            from_user=self.user,
            to_user=self.another_user,
            obj=self.project,
        )

    def test_revoke_project_invitation(self):
        url = reverse("invitations_revoke", args=[self.invitation.pk])

        self.client.logout()
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 1)

        self.client.force_login(self.another_user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Invitation.objects.all().count(), 1)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_REVOKED)
        self.assertEqual(queryset.count(), 0)

        self.client.force_login(self.user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.user)
        self.assertEqual(auditlog.project, self.project)
        self.assertEqual(
            auditlog.data,
            {
                "id": self.invitation.pk,
                "from_user": {
                    "id": self.user.pk,
                    "username": self.user.username,
                },
                "to_user": {
                    "id": self.another_user.pk,
                    "username": self.another_user.username,
                },
                "object_type": "project",
                "object": {
                    "id": self.project.pk,
                    "slug": self.project.slug,
                    "organization": {
                        "id": self.organization.pk,
                        "slug": self.organization.slug,
                    },
                },
                "to_email": None,
            },
        )

    def test_revoke_organization_invitation(self):
        url = reverse("invitations_revoke", args=[self.invitation.pk])
        self.invitation.object = self.organization
        self.invitation.save()

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 1)

        self.client.force_login(self.another_user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Invitation.objects.all().count(), 1)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_REVOKED)
        self.assertEqual(queryset.count(), 0)

        self.client.force_login(self.user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.user)
        self.assertEqual(auditlog.organization, self.organization)
        self.assertEqual(
            auditlog.data,
            {
                "id": self.invitation.pk,
                "from_user": {
                    "id": self.user.pk,
                    "username": self.user.username,
                },
                "to_user": {
                    "id": self.another_user.pk,
                    "username": self.another_user.username,
                },
                "object_type": "organization",
                "object": {
                    "id": self.organization.pk,
                    "slug": self.organization.slug,
                },
                "to_email": None,
            },
        )

    def test_revoke_team_invitation(self):
        url = reverse("invitations_revoke", args=[self.invitation.pk])
        self.invitation.object = self.team
        self.invitation.save()

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 1)

        self.client.force_login(self.another_user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Invitation.objects.all().count(), 1)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_REVOKED)
        self.assertEqual(queryset.count(), 0)

        self.client.force_login(self.user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.user)
        self.assertEqual(auditlog.organization, self.organization)
        self.assertEqual(
            auditlog.data,
            {
                "id": self.invitation.pk,
                "from_user": {
                    "id": self.user.pk,
                    "username": self.user.username,
                },
                "to_user": {
                    "id": self.another_user.pk,
                    "username": self.another_user.username,
                },
                "object_type": "team",
                "object": {
                    "id": self.team.pk,
                    "slug": self.team.slug,
                    "organization": {
                        "id": self.organization.pk,
                        "slug": self.organization.slug,
                    },
                },
                "to_email": None,
            },
        )

    def test_revoke_expired_invitation(self):
        url = reverse("invitations_revoke", args=[self.invitation.pk])
        self.invitation.expiration_date = timezone.now() - timezone.timedelta(days=5)
        self.invitation.save()
        self.assertTrue(self.invitation.expired)

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 1)

        self.client.force_login(self.another_user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Invitation.objects.all().count(), 1)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_REVOKED)
        self.assertEqual(queryset.count(), 0)

        self.client.force_login(self.user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.user)
        self.assertEqual(auditlog.project, self.project)
        self.assertEqual(
            auditlog.data,
            {
                "id": self.invitation.pk,
                "from_user": {
                    "id": self.user.pk,
                    "username": self.user.username,
                },
                "to_user": {
                    "id": self.another_user.pk,
                    "username": self.another_user.username,
                },
                "object_type": "project",
                "object": {
                    "id": self.project.pk,
                    "slug": self.project.slug,
                    "organization": {
                        "id": self.organization.pk,
                        "slug": self.organization.slug,
                    },
                },
                "to_email": None,
            },
        )

    def test_revoke_email_invitation(self):
        url = reverse("invitations_revoke", args=[self.invitation.pk])
        self.invitation.to_user = None
        self.invitation.to_email = self.email
        self.invitation.save()

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 1)

        self.client.force_login(self.another_user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Invitation.objects.all().count(), 1)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_REVOKED)
        self.assertEqual(queryset.count(), 0)

        self.client.force_login(self.user)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.user)
        self.assertEqual(auditlog.project, self.project)
        self.assertEqual(
            auditlog.data,
            {
                "id": self.invitation.pk,
                "from_user": {
                    "id": self.user.pk,
                    "username": self.user.username,
                },
                "to_user": None,
                "to_email": self.email,
                "object_type": "project",
                "object": {
                    "id": self.project.pk,
                    "slug": self.project.slug,
                    "organization": {
                        "id": self.organization.pk,
                        "slug": self.organization.slug,
                    },
                },
            },
        )

    def test_accept_project_invitation(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_ACCEPTED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url, data={"accept": True})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertIn(self.another_user, self.project.users.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.project, self.project)

    def test_accept_organization_invitation(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.object = self.organization
        self.invitation.save()

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_ACCEPTED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url, data={"accept": True})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertIn(self.another_user, self.organization.owners.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.organization, self.organization)

    def test_accept_team_invitation(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.object = self.team
        self.invitation.save()

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_ACCEPTED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url, data={"accept": True})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertTrue(
            self.team.teammember_set.filter(member=self.another_user).exists()
        )

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.organization, self.organization)

    def test_accept_expired_invitation(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.expiration_date = timezone.now() - timezone.timedelta(days=5)
        self.invitation.save()
        self.assertTrue(self.invitation.expired)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_ACCEPTED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url, data={"accept": True})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Invitation.objects.all().count(), 1)
        self.assertNotIn(self.another_user, self.project.users.all())

        self.assertEqual(queryset.count(), 0)

    def test_accept_invitation_user(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.client.force_login(self.user)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_ACCEPTED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url, data={"accept": True})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertIn(self.another_user, self.project.users.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.organization, self.organization)

    def test_accept_invitation_another_user(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.client.force_login(self.another_user)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_ACCEPTED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url, data={"accept": True})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertIn(self.another_user, self.project.users.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.organization, self.organization)

    def test_decline_project_invitation(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_DECLINED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertNotIn(self.another_user, self.project.users.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.project, self.project)

    def test_decline_organization_invitation(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.object = self.organization
        self.invitation.save()

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_DECLINED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertNotIn(self.another_user, self.organization.owners.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.organization, self.organization)

    def test_decline_team_invitation(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.object = self.team
        self.invitation.save()

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_DECLINED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertFalse(
            self.team.teammember_set.filter(member=self.another_user).exists()
        )

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.organization, self.organization)

    def test_decline_expired_invitation(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.expiration_date = timezone.now() - timezone.timedelta(days=5)
        self.invitation.save()
        self.assertTrue(self.invitation.expired)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_DECLINED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertNotIn(self.another_user, self.project.users.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.project, self.project)

    def test_accept_email_invitation_logged_in(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.to_user = None
        self.invitation.to_email = self.email
        self.invitation.save()

        self.client.force_login(self.another_user)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_ACCEPTED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url, data={"accept": True})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertIn(self.another_user, self.project.users.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, self.another_user)
        self.assertEqual(auditlog.project, self.project)

    def test_accept_email_invitation_anonymous_user(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.to_user = None
        self.invitation.to_email = self.email
        self.invitation.object = self.team
        self.invitation.save()

        r = self.client.post(url, data={"accept": True})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["location"], reverse("account_signup"))
        self.assertEqual(Invitation.objects.all().count(), 1)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_ACCEPTED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(
            reverse("account_signup"),
            data={
                "email": self.email,
                "username": "new",
                "password1": "123456",
                "password2": "123456",
            },
        )
        self.assertEqual(r.status_code, 302)

        user = User.objects.get(username="new")
        self.assertTrue(
            user.emailaddress_set.filter(email=self.email, verified=True).exists()
        )

        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertTrue(self.team.teammember_set.filter(member=user).exists())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, user)
        self.assertEqual(auditlog.organization, self.organization)

    def test_decline_email_invitation_logged_in(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.to_user = None
        self.invitation.to_email = self.email
        self.invitation.save()

        self.client.force_login(self.another_user)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_DECLINED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertNotIn(self.another_user, self.project.users.all())

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, None)
        self.assertEqual(auditlog.project, self.project)

    def test_decline_email_invitation_anonymous_user(self):
        url = reverse("invitations_redeem", args=[self.invitation.token])
        self.invitation.to_user = None
        self.invitation.to_email = self.email
        self.invitation.save()

        self.assertEqual(self.project.users.all().count(), 1)

        queryset = AuditLog.objects.filter(action=AuditLog.INVITATION_DECLINED)
        self.assertEqual(queryset.count(), 0)

        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Invitation.objects.all().count(), 0)
        self.assertEqual(self.project.users.all().count(), 1)

        # Audit log was created.
        self.assertEqual(queryset.count(), 1)
        auditlog = queryset.get()
        self.assertEqual(auditlog.user, None)
        self.assertEqual(auditlog.project, self.project)

    def test_migrate_team_invitation_on_the_fly(self):
        email = "test@example.com"
        team_invite = get(
            TeamInvite, organization=self.organization, team=self.team, email=email
        )
        self.assertFalse(Invitation.objects.filter(token=team_invite.hash).exists())

        url = reverse("invitations_redeem", args=[team_invite.hash])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        self.assertFalse(TeamInvite.objects.filter(hash=team_invite.hash).exists())
        invitation = Invitation.objects.get(token=team_invite.hash)

        self.assertTrue(invitation.object, self.team)
        self.assertTrue(invitation.token, team_invite.hash)
        self.assertTrue(invitation.from_user, self.user)
        self.assertTrue(invitation.to_email, email)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(TeamInvite.objects.filter(hash=team_invite.hash).exists())
        self.assertEqual(Invitation.objects.get(token=team_invite.hash), invitation)
