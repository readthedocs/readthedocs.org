import csv
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import itertools
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get
from PIL import Image

from readthedocs.audit.models import AuditLog
from readthedocs.core.utils import slugify
from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.base import RequestFactoryTestMixin
from readthedocs.subscriptions.constants import TYPE_AUDIT_LOGS
from readthedocs.subscriptions.products import RTDProductFeature


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationViewTests(RequestFactoryTestMixin, TestCase):

    """Organization views tests."""

    def setUp(self):
        self.owner = get(User, username="owner", email="owner@example.com")
        self.owner.emailaddress_set.create(email=self.owner.email, verified=True)
        self.project = get(Project)
        self.organization = get(
            Organization,
            name="test-org",
            slug="test-org",
            owners=[self.owner],
            projects=[self.project],
        )
        self.team = get(Team, organization=self.organization)
        self.client.force_login(self.owner)

    def test_update(self):
        org_slug = self.organization.slug
        resp = self.client.post(
            reverse("organization_edit", args=[self.organization.slug]),
            data={
                "name": "New name",
                "email": "dev@example.com",
                "description": "Description",
                "url": "https://readthedocs.org",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "New name")
        self.assertEqual(self.organization.email, "dev@example.com")
        self.assertEqual(self.organization.url, "https://readthedocs.org")
        self.assertEqual(self.organization.description, "Description")
        # The slug hasn't changed.
        self.assertEqual(self.organization.slug, org_slug)

    def _create_image(self, size=(100, 100), format='PNG'):
        """Helper to create an in-memory image file."""
        image = Image.new(mode='RGB', size=size, color=(0, 0, 0))
        image_bytes = io.BytesIO()
        image.save(image_bytes, format=format)
        image_bytes.seek(0)
        return image_bytes

    def test_update_avatar(self):
        avatar_file = SimpleUploadedFile(
            name='test.png',
            content=self._create_image(size=(100, 100)).read(),
            content_type='image/png'
        )

        response = self.client.post(
            reverse("organization_edit", args=[self.organization.slug]),
            {
                "name": "New name",
                "email": "dev@example.com",
                "description": "Description",
                "url": "https://readthedocs.org",
                "avatar": avatar_file,
            },
        )
        assert response.status_code == 302
        self.organization.refresh_from_db()
        assert self.organization.avatar
        assert self.organization.avatar.name.startswith("avatars/organizations/")
        assert self.organization.avatar.name.endswith(".png")

    def test_update_avatar_invalid_dimensions(self):
        avatar_file = SimpleUploadedFile(
            name='test.png',
            content=self._create_image(size=(1000, 1000)).read(),
            content_type='image/png'
        )

        response = self.client.post(
            reverse("organization_edit", args=[self.organization.slug]),
            {
                "name": "New name",
                "email": "dev@example.com",
                "description": "Description",
                "url": "https://readthedocs.org",
                "avatar": avatar_file,
            },
        )
        assert response.status_code == 200
        form = response.context_data['form']
        assert not form.is_valid()
        assert 'avatar' in form.errors
        assert "The image dimensions cannot exceed" in form.errors['avatar'][0]

    def test_update_avatar_invalid_image(self):
        avatar_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image file.',
            content_type='text/plain'
        )

        response = self.client.post(
            reverse("organization_edit", args=[self.organization.slug]),
            {
                "name": "New name",
                "email": "dev@example.com",
                "description": "Description",
                "url": "https://readthedocs.org",
                "avatar": avatar_file,
            },
        )
        assert response.status_code == 200
        form = response.context_data['form']
        assert not form.is_valid()
        assert 'avatar' in form.errors
        assert "Upload a valid image." in form.errors['avatar'][0]

    def test_update_avatar_invalid_extension(self):
        avatar_file = SimpleUploadedFile(
            name='test.gif',
            content=self._create_image(size=(100, 100), format='GIF').read(),
            content_type='image/gif'
        )

        response = self.client.post(
            reverse("organization_edit", args=[self.organization.slug]),
            {
                "name": "New name",
                "email": "dev@example.com",
                "description": "Description",
                "url": "https://readthedocs.org",
                "avatar": avatar_file,
            },
        )
        assert response.status_code == 200
        form = response.context_data['form']
        assert not form.is_valid()
        assert 'avatar' in form.errors
        assert "File extension “gif” is not allowed" in form.errors['avatar'][0]

    def test_change_name(self):
        """
        Changing the name of the organization won't change the slug.

        So changing it to something that will generate an existing slug
        shouldn't matter.
        """
        new_name = "Test Org"
        org_slug = self.organization.slug
        self.assertNotEqual(new_name, self.organization.name)
        self.assertEqual(slugify(new_name), org_slug)

        resp = self.client.post(
            reverse("organization_edit", args=[self.organization.slug]),
            data={"name": new_name},
        )
        self.assertEqual(resp.status_code, 302)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, new_name)
        self.assertEqual(self.organization.slug, org_slug)

    def test_delete(self):
        """Delete organization on post."""
        resp = self.client.post(
            reverse("organization_delete", args=[self.organization.slug])
        )
        self.assertEqual(resp.status_code, 302)

        self.assertFalse(Organization.objects.filter(pk=self.organization.pk).exists())
        self.assertFalse(Team.objects.filter(pk=self.team.pk).exists())
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_add_owner(self):
        url = reverse("organization_owner_add", args=[self.organization.slug])
        user = get(User, username="test-user", email="test-user@example.com")
        user.emailaddress_set.create(email=user.email, verified=False)

        user_b = get(User, username="test-user-b", email="test-user-b@example.com")
        user_b.emailaddress_set.create(email=user_b.email, verified=True)

        # Adding an already owner.
        for username in [self.owner.username, self.owner.email]:
            resp = self.client.post(url, data={"username_or_email": username})
            form = resp.context_data["form"]
            self.assertFalse(form.is_valid())
            self.assertIn("is already an owner", form.errors["username_or_email"][0])

        # Unknown user.
        resp = self.client.post(url, data={"username_or_email": "non-existent"})
        form = resp.context_data["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("does not exist", form.errors["username_or_email"][0])

        # From an unverified email.
        resp = self.client.post(url, data={"username_or_email": user.email})
        form = resp.context_data["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("does not exist", form.errors["username_or_email"][0])

        # Using a username.
        self.assertFalse(user in self.organization.owners.all())
        resp = self.client.post(url, data={"username_or_email": user.username})
        self.assertEqual(resp.status_code, 302)
        qs = Invitation.objects.for_object(self.organization)
        self.assertEqual(qs.count(), 1)
        invitation = qs.first()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, user)
        self.assertEqual(invitation.to_email, None)
        self.assertNotIn(user, self.organization.owners.all())

        # Using an email.
        self.assertFalse(user_b in self.organization.owners.all())
        resp = self.client.post(url, data={"username_or_email": user_b.email})
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(qs.count(), 2)
        invitation = qs.last()
        self.assertEqual(invitation.from_user, self.owner)
        self.assertEqual(invitation.to_user, user_b)
        self.assertEqual(invitation.to_email, None)
        self.assertNotIn(user_b, self.organization.owners.all())


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_DEFAULT_FEATURES=dict(
        [RTDProductFeature(type=TYPE_AUDIT_LOGS, value=90).to_item()]
    ),
)
class OrganizationSecurityLogTests(TestCase):
    def setUp(self):
        self.owner = get(User, username="owner")
        self.member = get(User, username="member")
        self.project = get(Project, slug="project")
        self.project_b = get(Project, slug="project-b")
        self.organization = get(
            Organization,
            owners=[self.owner],
            projects=[self.project, self.project_b],
        )
        self.team = get(
            Team,
            organization=self.organization,
            members=[self.member],
        )

        self.another_owner = get(User, username="another-owner")
        self.another_member = get(User, username="another-member")
        self.another_project = get(Project, slug="another-project")
        self.another_organization = get(
            Organization,
            owners=[self.another_owner],
            projects=[self.another_project],
        )
        self.another_team = get(
            Team,
            organization=self.another_organization,
            members=[self.another_member],
        )
        self.client.force_login(self.owner)

        actions = [
            AuditLog.AUTHN,
            AuditLog.AUTHN_FAILURE,
            AuditLog.LOGOUT,
            AuditLog.PAGEVIEW,
            AuditLog.DOWNLOAD,
        ]
        ips = [
            "10.10.10.1",
            "10.10.10.2",
        ]
        users = [self.owner, self.member, self.another_owner, self.another_member]
        projects = [self.project, self.project_b, self.another_project]
        AuditLog.objects.all().delete()
        for action, ip, user in itertools.product(actions, ips, users):
            get(
                AuditLog,
                user=user,
                action=action,
                ip=ip,
            )
            for project in projects:
                get(
                    AuditLog,
                    user=user,
                    action=action,
                    project=project,
                    ip=ip,
                )

        self.url = reverse("organization_security_log", args=[self.organization.slug])
        self.queryset = AuditLog.objects.filter(
            log_organization_id=self.organization.pk
        )

    def test_list_security_logs(self):
        # Show logs for self.organization only.
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(auditlogs, self.queryset)

        # Show logs filtered by project.
        resp = self.client.get(self.url + "?project=project")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(
            auditlogs, self.queryset.filter(log_project_slug="project")
        )

        resp = self.client.get(self.url + "?project=another-project")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertEqual(auditlogs.count(), 0)

        # Show logs filtered by IP.
        ip = "10.10.10.2"
        resp = self.client.get(self.url + f"?ip={ip}")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(auditlogs, self.queryset.filter(ip=ip))

        # Show logs filtered by action.
        for action in [
            AuditLog.AUTHN,
            AuditLog.AUTHN_FAILURE,
            AuditLog.PAGEVIEW,
            AuditLog.DOWNLOAD,
        ]:
            resp = self.client.get(self.url + f"?action={action}")
            self.assertEqual(resp.status_code, 200)
            auditlogs = resp.context_data["object_list"]
            self.assertQuerySetEqual(auditlogs, self.queryset.filter(action=action))

        # Show logs filtered by user.
        resp = self.client.get(self.url + "?user=member")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(
            auditlogs, self.queryset.filter(log_user_username="member")
        )

    @mock.patch("django.utils.timezone.now")
    def test_filter_by_date(self, now_mock):
        date = timezone.datetime(year=2021, month=1, day=15)
        now_mock.return_value = date
        self.organization.pub_date = date
        self.organization.save()

        date = timezone.datetime(year=2021, month=3, day=10)
        AuditLog.objects.all().update(created=date)

        date = timezone.datetime(year=2021, month=2, day=13)
        AuditLog.objects.filter(action=AuditLog.AUTHN).update(created=date)

        date = timezone.datetime(year=2021, month=4, day=24)
        AuditLog.objects.filter(action=AuditLog.AUTHN_FAILURE).update(created=date)

        resp = self.client.get(self.url + "?date_before=2020-10-10")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertEqual(auditlogs.count(), 0)

        resp = self.client.get(self.url + "?date_after=2023-10-10")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertEqual(auditlogs.count(), 0)

        resp = self.client.get(self.url + "?date_before=2021-03-9")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(auditlogs, self.queryset.filter(action=AuditLog.AUTHN))

        resp = self.client.get(self.url + "?date_after=2021-03-11")
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(
            auditlogs, self.queryset.filter(action=AuditLog.AUTHN_FAILURE)
        )

        resp = self.client.get(
            self.url + "?date_after=2021-01-01&date_before=2021-03-10"
        )
        self.assertEqual(resp.status_code, 200)
        auditlogs = resp.context_data["object_list"]
        self.assertQuerySetEqual(
            auditlogs, self.queryset.exclude(action=AuditLog.AUTHN_FAILURE)
        )

    def test_download_csv(self):
        self.assertEqual(AuditLog.objects.count(), 160)
        resp = self.client.get(self.url, {"download": "true"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/csv")

        # convert streaming data to csv format
        content = [
            line.decode() for line in b"".join(resp.streaming_content).splitlines()
        ]
        csv_data = list(csv.reader(content))
        # All records + the header.
        self.assertEqual(
            len(csv_data),
            AuditLog.objects.filter(log_organization_id=self.organization.pk).count()
            + 1,
        )


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationInviteViewTests(RequestFactoryTestMixin, TestCase):

    """Tests for invite handling in views."""

    def setUp(self):
        self.owner = get(User)
        self.organization = get(
            Organization,
            owners=[self.owner],
        )
        self.team = get(Team, organization=self.organization)

    def test_redirect(self):
        token = "123345"
        resp = self.client.get(reverse("organization_invite_redeem", args=[token]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["location"], reverse("invitations_redeem", args=[token]))


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationSignupTestCase(TestCase):
    def tearDown(self):
        cache.clear()

    def test_organization_signup(self):
        self.assertEqual(Organization.objects.count(), 0)
        user = get(User)
        self.client.force_login(user)
        data = {
            "name": "Testing Organization",
            "email": "billing@email.com",
            "slug": "testing-organization",
        }
        resp = self.client.post(reverse("organization_create"), data=data)
        self.assertEqual(Organization.objects.count(), 1)

        org = Organization.objects.first()
        self.assertEqual(org.name, "Testing Organization")
        self.assertEqual(org.email, "billing@email.com")
        self.assertRedirects(
            resp,
            reverse("organization_detail", kwargs={"slug": org.slug}),
        )


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(TYPE_AUDIT_LOGS, value=90).to_item()]),
)
class OrganizationUnspecifiedChooser(TestCase):
    def setUp(self):
        self.owner = get(User, username="owner")
        self.member = get(User, username="member")
        self.project = get(Project, slug="project")
        self.organization = get(
            Organization,
            owners=[self.owner],
            projects=[self.project],
        )
        self.team = get(
            Team,
            organization=self.organization,
            members=[self.member],
        )
        self.another_organization = get(
            Organization,
            owners=[self.owner],
            projects=[self.project],
        )
        self.client.force_login(self.owner)

    def test_choose_organization_edit(self):
        """
        Verify that the choose page works.
        """
        self.assertEqual(Organization.objects.count(), 2)
        resp = self.client.get(
            reverse("organization_choose", kwargs={"next_name": "organization_edit"})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(
            resp, reverse("organization_edit", kwargs={"slug": self.organization.slug})
        )
        self.assertContains(
            resp,
            reverse(
                "organization_edit", kwargs={"slug": self.another_organization.slug}
            ),
        )


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(TYPE_AUDIT_LOGS, value=90).to_item()]),
)
class OrganizationUnspecifiedSingleOrganizationRedirect(TestCase):
    def setUp(self):
        self.owner = get(User, username="owner")
        self.member = get(User, username="member")
        self.project = get(Project, slug="project")
        self.organization = get(
            Organization,
            owners=[self.owner],
            projects=[self.project],
        )
        self.client.force_login(self.owner)

    def test_unspecified_slug_redirects_to_organization_edit(self):
        self.assertEqual(Organization.objects.count(), 1)
        resp = self.client.get(
            reverse("organization_choose", kwargs={"next_name": "organization_edit"})
        )
        self.assertRedirects(
            resp, reverse("organization_edit", kwargs={"slug": self.organization.slug})
        )


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(TYPE_AUDIT_LOGS, value=90).to_item()]),
)
class OrganizationUnspecifiedNoOrganizationRedirect(TestCase):
    def setUp(self):
        self.owner = get(User, username="owner")
        self.member = get(User, username="member")
        self.project = get(Project, slug="project")
        self.client.force_login(self.owner)

    def test_choose_organization_edit(self):
        self.assertEqual(Organization.objects.count(), 0)
        resp = self.client.get(
            reverse("organization_choose", kwargs={"next_name": "organization_edit"})
        )
        self.assertContains(resp, "Your user is not a member of an organization yet")
