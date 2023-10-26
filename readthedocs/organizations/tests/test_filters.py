from unittest import mock

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from readthedocs.organizations.filters import (
    OrganizationListFilterSet,
    OrganizationProjectListFilterSet,
)
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class OrganizationFilterTestCase(TestCase):
    def setUp(self):
        self.owner = fixture.get(User)
        self.user = fixture.get(User)
        self.project = fixture.get(Project)

        self.organization = fixture.get(
            Organization,
            owners=[self.owner],
            projects=[self.project],
            stripe_id="1234",
        )
        self.team = fixture.get(
            Team,
            access="admin",
            organization=self.organization,
            members=[self.user],
            projects=[self.project],
        )
        self.client.force_login(self.user)

        # Create extra objects just to ensure there are no extra objects in our
        # filter querysets
        self.other_owner = fixture.get(User)
        self.other_user = fixture.get(User)
        self.other_project = fixture.get(Project)
        self.other_organization = fixture.get(
            Organization,
            owners=[self.other_owner],
            projects=[self.other_project],
        )
        self.other_team = fixture.get(
            Team,
            access="admin",
            organization=self.other_organization,
        )


class OrganizationFilterTests(OrganizationFilterTestCase):
    def setUp(self):
        super().setUp()
        self.queryset = Organization.objects.for_user(self.owner)
        self.request = RequestFactory().get("")
        self.request.user = self.user

    def test_unfiltered_queryset(self):
        """No active filters returns full queryset."""
        filter = OrganizationListFilterSet(
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs, self.queryset, transform=lambda o: o, ordered=False
        )

    def test_filtered_queryset_choice(self):
        """Valid project choice returns expected results."""
        filter = OrganizationListFilterSet(
            {"slug": self.organization.slug},
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs, [self.organization.pk], transform=lambda o: o.pk, ordered=False
        )

    def test_filtered_queryset_invalid_choice(self):
        """Invalid project choice returns the original queryset."""
        filter = OrganizationListFilterSet(
            {"slug": self.other_organization.slug},
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs,
            self.queryset,
            transform=lambda o: o,
            ordered=False,
        )

    def test_organization_filter_choices(self):
        filter = OrganizationListFilterSet(
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertEqual(
            list(filter.filters["slug"].field.choices),
            [
                ("", "All organizations"),
                (mock.ANY, self.organization.slug),
            ],
        )


class OrganizationProjectFilterTests(OrganizationFilterTestCase):
    def setUp(self):
        super().setUp()
        self.team_empty = fixture.get(
            Team,
            access="admin",
            organization=self.organization,
            members=[self.user],
            projects=[],
        )
        self.queryset = (
            Project.objects.for_user(self.owner)
            .filter(organizations=self.organization)
            .all()
        )
        self.request = RequestFactory().get("")
        self.request.user = self.user

    def test_unfiltered_queryset(self):
        """No active filters returns full queryset."""
        filter = OrganizationProjectListFilterSet(
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs, self.queryset, transform=lambda o: o, ordered=False
        )

    def test_filtered_queryset_project_choice(self):
        """Valid project choice returns expected results."""
        filter = OrganizationProjectListFilterSet(
            {"slug": self.project.slug},
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs,
            [self.project.pk],
            transform=lambda o: o.pk,
            ordered=False,
        )

    def test_filtered_queryset_project_invalid_choice(self):
        """Invalid project choice returns the original queryset."""
        filter = OrganizationProjectListFilterSet(
            {"slug": self.other_project.slug},
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs,
            self.queryset,
            transform=lambda o: o,
            ordered=False,
        )

    def test_filtered_queryset_team_choice(self):
        """Valid team choice returns expected results."""
        filter = OrganizationProjectListFilterSet(
            {"teams__slug": self.team.slug},
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs,
            [self.project.pk],
            transform=lambda o: o.pk,
            ordered=False,
        )
        filter = OrganizationProjectListFilterSet(
            {"teams__slug": self.team_empty.slug},
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs,
            [],
            transform=lambda o: o.pk,
            ordered=False,
        )

    def test_filtered_queryset_team_invalid_choice(self):
        """Invalid team choice returns the original queryset."""
        filter = OrganizationProjectListFilterSet(
            {"teams__slug": self.other_team.slug},
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertQuerySetEqual(
            filter.qs,
            self.queryset,
            transform=lambda o: o,
            ordered=False,
        )

    def test_project_filter_choices(self):
        """Project filter choices limited to organization projects."""
        filter = OrganizationProjectListFilterSet(
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertEqual(
            list(filter.filters["slug"].field.choices),
            [
                ("", "All projects"),
                (mock.ANY, self.project.slug),
            ],
        )

    def test_team_filter_choices(self):
        """Team filter choices limited to organization teams."""
        filter = OrganizationProjectListFilterSet(
            queryset=self.queryset,
            request=self.request,
            organization=self.organization,
        )
        self.assertEqual(
            list(filter.filters["teams__slug"].field.choices),
            [
                ("", "All teams"),
                (mock.ANY, self.team.slug),
                (mock.ANY, self.team_empty.slug),
            ],
        )
