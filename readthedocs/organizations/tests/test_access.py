import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization, OrganizationOwner, Team
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.utils import create_user


class OrganizationAccessMixin:
    url_responses = {}

    def login(self):
        raise NotImplementedError

    def is_admin(self):
        raise NotImplementedError

    def assertResponse(self, path, method=None, data=None, **kwargs):
        self.login()
        if method is None:
            method = self.client.get
        if data is None:
            data = {}
        response = method(path, data=data)
        response_attrs = {
            "status_code": kwargs.pop("status_code", 200),
        }
        response_attrs.update(kwargs)
        response_attrs.update(self.url_responses.get(path, {}))
        for key, val in list(response_attrs.items()):
            self.assertEqual(getattr(response, key), val)
        return response

    def setUp(self):
        # Previous Fixtures
        self.eric = create_user(username="eric", password="test")
        self.test = create_user(username="test", password="test")
        self.tester = create_user(username="tester", password="test")
        self.project = fixture.get(Project, slug="pip")
        self.organization = fixture.get(
            Organization,
            name="Mozilla",
            slug="mozilla",
            projects=[self.project],
        )
        self.team = fixture.get(
            Team,
            name="Foobar",
            slug="foobar",
            organization=self.organization,
            members=[self.test],
        )
        self.owner = fixture.get(
            OrganizationOwner,
            owner=self.eric,
            organization=self.organization,
        )

    def test_organization_list(self):
        self.assertResponse("/organizations/", status_code=200)

    def test_organization_details(self):
        self.assertResponse("/organizations/mozilla/", status_code=200)
        self.assertResponse("/organizations/mozilla/edit/", status_code=200)

    def test_organization_owners_regression(self):
        """Regression test for paths that have been moved."""
        self.assertEqual(self.organization.owners.count(), 1)
        self.assertResponse("/organizations/mozilla/owners/", status_code=200)
        self.assertResponse(
            "/organizations/mozilla/owners/add/",
            method=self.client.post,
            data={"username_or_email": "tester"},
            status_code=302,
        )
        if self.is_admin():
            invitation = Invitation.objects.for_object(self.organization).first()
            invitation.redeem()
            self.assertEqual(self.organization.owners.count(), 2)
        else:
            self.assertFalse(Invitation.objects.for_object(self.organization).exists())
            self.assertEqual(self.organization.owners.count(), 1)
        self.assertResponse(
            "/organizations/mozilla/owners/delete/",
            method=self.client.post,
            data={"user": "tester"},
            status_code=404,
        )
        if self.is_admin():
            self.assertEqual(self.organization.owners.count(), 2)
        else:
            self.assertEqual(self.organization.owners.count(), 1)

    def test_organization_owners(self):
        self.assertEqual(self.organization.owners.count(), 1)
        self.assertResponse("/organizations/mozilla/owners/", status_code=200)
        self.assertResponse(
            "/organizations/mozilla/owners/add/",
            method=self.client.post,
            data={"username_or_email": "tester"},
            status_code=302,
        )
        if self.is_admin():
            invitation = Invitation.objects.for_object(self.organization).first()
            invitation.redeem()
            self.assertEqual(self.organization.owners.count(), 2)
            owner = OrganizationOwner.objects.get(
                organization=self.organization,
                owner__username="tester",
            )
            self.assertResponse(
                "/organizations/mozilla/owners/{}/delete/".format(owner.pk),
                method=self.client.post,
                data={"user": "tester"},
                status_code=302,
            )
            self.assertEqual(self.organization.owners.count(), 1)
        else:
            self.assertFalse(
                OrganizationOwner.objects.filter(
                    organization=self.organization,
                    owner__username="tester",
                ).exists(),
            )
            self.assertEqual(self.organization.owners.count(), 1)

    def test_organization_members_regression(self):
        """Tests for regression against old member functionality."""
        self.assertEqual(self.organization.members.count(), 2)
        self.assertResponse(
            "/organizations/mozilla/members/",
            status_code=200,
        )
        self.assertResponse(
            "/organizations/mozilla/members/add/",
            method=self.client.post,
            data={"user": "tester"},
            status_code=404,
        )
        if self.is_admin():
            self.assertEqual(self.organization.members.count(), 2)
        else:
            self.assertEqual(self.organization.members.count(), 2)

        self.assertResponse(
            "/organizations/mozilla/members/delete/",
            method=self.client.post,
            data={"user": "tester"},
            status_code=404,
        )
        self.assertEqual(self.organization.members.count(), 2)

    def test_organization_teams(self):
        self.assertEqual(self.organization.teams.count(), 1)
        self.assertResponse("/organizations/mozilla/teams/", status_code=200)
        user = User.objects.get(username="test")
        project = Project.objects.get(slug="pip")
        self.assertResponse(
            "/organizations/mozilla/teams/add/",
            method=self.client.post,
            data={
                "name": "more-foobar",
                "access": "readonly",
            },
            status_code=302,
        )
        if self.is_admin():
            self.assertEqual(self.organization.teams.count(), 2)
            self.assertEqual(self.organization.members.count(), 2)
            self.assertResponse(
                "/organizations/mozilla/teams/more-foobar/delete/",
                method=self.client.post,
                status_code=302,
            )
        else:
            self.assertEqual(self.organization.teams.count(), 1)
            self.assertFalse(
                self.organization.teams.filter(name="foobar").exists(),
            )
            self.assertEqual(self.organization.members.count(), 2)
        self.assertEqual(self.organization.teams.count(), 1)


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationOwnerAccess(OrganizationAccessMixin, TestCase):

    """Test organization paths with authed org owner."""

    def login(self):
        return self.client.login(username="eric", password="test")

    def is_admin(self):
        return True


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationMemberAccess(OrganizationAccessMixin, TestCase):

    """Test organization paths with authed org member."""

    url_responses = {
        "/organizations/": {"status_code": 200},
        "/organizations/mozilla/": {"status_code": 200},
        "/organizations/mozilla/members/": {"status_code": 200},
        "/organizations/mozilla/teams/": {"status_code": 200},
    }

    def assertResponse(self, path, method=None, data=None, **kwargs):
        kwargs["status_code"] = 404
        super().assertResponse(path, method, data, **kwargs)

    def login(self):
        return self.client.login(username="test", password="test")

    def is_admin(self):
        return False


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationNonmemberAccess(OrganizationAccessMixin, TestCase):

    """Test organization paths with authed but non-org user."""

    url_responses = {
        "/organizations/": {"status_code": 200},
    }

    def assertResponse(self, path, method=None, data=None, **kwargs):
        kwargs["status_code"] = 404
        super().assertResponse(path, method, data, **kwargs)

    def login(self):
        return self.client.login(username="tester", password="test")

    def is_admin(self):
        return False
