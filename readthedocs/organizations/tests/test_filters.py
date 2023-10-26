import django_dynamic_fixture as fixture
import pytest
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from pytest_django.asserts import assertQuerySetEqual

from readthedocs.organizations.filters import (
    OrganizationListFilterSet,
    OrganizationProjectListFilterSet,
    OrganizationTeamListFilterSet,
    OrganizationTeamMemberListFilterSet,
)
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


@pytest.mark.django_db
class OrganizationFilterTestCase:
    @pytest.fixture(autouse=True)
    def set_up(self, settings):
        settings.RTD_ALLOW_ORGANIZATIONS = True

        self.owner = fixture.get(User)
        self.user = fixture.get(User)
        self.project = fixture.get(Project)

        self.organization = fixture.get(
            Organization,
            owners=[self.owner],
            projects=[self.project],
        )
        self.team = fixture.get(
            Team,
            access="admin",
            organization=self.organization,
            members=[self.user],
            projects=[self.project],
        )
        self.team_empty = fixture.get(
            Team,
            access="readonly",
            organization=self.organization,
            members=[],
            projects=[],
        )

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
            members=[self.other_user],
            projects=[self.other_project],
        )

        self.set_up_extra()

    def set_up_extra(self):
        pass


class TestOrganizationFilterSet(OrganizationFilterTestCase):
    def get_filterset_for_user(self, user, *args, **kwargs):
        request = RequestFactory().get("")
        request.user = user
        queryset = Organization.objects.for_user(user)
        kwargs.update(
            {
                "queryset": queryset,
                "request": request,
            }
        )
        return OrganizationListFilterSet(*args, **kwargs)

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization),
            lambda self: (self.owner, self.organization),
            lambda self: (self.other_user, self.other_organization),
            lambda self: (self.other_owner, self.other_organization),
        ],
    )
    def test_unfiltered_queryset(self, get_params):
        """No active filters returns full queryset."""
        (user, organization) = get_params(self)
        filter = self.get_filterset_for_user(user, organization=organization)
        assertQuerySetEqual(
            filter.qs,
            [organization],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization),
            lambda self: (self.owner, self.organization),
            lambda self: (self.other_user, self.other_organization),
            lambda self: (self.other_owner, self.other_organization),
        ],
    )
    def test_filtered_queryset_choice(self, get_params):
        """Valid project choice returns expected results."""
        (user, organization) = get_params(self)
        request = RequestFactory().get("")
        request.user = user
        queryset = Organization.objects.for_user(user)
        filter = OrganizationListFilterSet(
            {"slug": organization.slug},
            queryset=queryset,
            request=request,
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            [organization],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, self.other_organization),
            lambda self: (self.owner, self.organization, self.other_organization),
            lambda self: (self.other_user, self.other_organization, self.organization),
            lambda self: (self.other_owner, self.other_organization, self.organization),
        ],
    )
    def test_filtered_queryset_invalid_choice(self, get_params):
        """Invalid project choice returns the original queryset."""
        (user, organization, wrong_organization) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            {"slug": wrong_organization.slug},
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            [organization],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization),
            lambda self: (self.owner, self.organization),
            lambda self: (self.other_user, self.other_organization),
            lambda self: (self.other_owner, self.other_organization),
        ],
    )
    def test_organization_filter_choices(self, get_params):
        (user, organization) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            organization=organization,
        )
        assert list(dict(filter.filters["slug"].field.choices).keys()) == [
            "",
            organization.slug,
        ]


class TestOrganizationProjectFilterSet(OrganizationFilterTestCase):
    def get_filterset_for_user(self, user, *args, **kwargs):
        request = RequestFactory().get("")
        request.user = user
        queryset = Project.objects.for_user(user).filter(
            organizations=kwargs.get("organization", self.organization)
        )
        kwargs.update(
            {
                "queryset": queryset,
                "request": request,
            }
        )
        return OrganizationProjectListFilterSet(*args, **kwargs)

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, self.project),
            lambda self: (self.owner, self.organization, self.project),
            lambda self: (self.other_user, self.other_organization, self.other_project),
            lambda self: (
                self.other_owner,
                self.other_organization,
                self.other_project,
            ),
        ],
    )
    def test_unfiltered_queryset(self, get_params):
        """No active filters returns full queryset."""
        (user, organization, project) = get_params(self)
        filter = self.get_filterset_for_user(user, organization=organization)
        assertQuerySetEqual(
            filter.qs,
            [project],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, self.project),
            lambda self: (self.owner, self.organization, self.project),
            lambda self: (self.other_user, self.other_organization, self.other_project),
            lambda self: (
                self.other_owner,
                self.other_organization,
                self.other_project,
            ),
        ],
    )
    def test_filtered_queryset_project_choice(self, get_params):
        """Valid project choice returns expected results."""
        (user, organization, project) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            {"slug": project.slug},
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            [project],
            transform=lambda o: o,
            ordered=False,
        )

    def test_filtered_queryset_project_invalid_choice(self):
        """Invalid project choice returns the original queryset."""
        filter = self.get_filterset_for_user(
            self.user,
            {"slug": self.other_project.slug},
            organization=self.organization,
        )
        assertQuerySetEqual(
            filter.qs,
            [self.project],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, self.team, [self.project]),
            lambda self: (self.owner, self.organization, self.team, [self.project]),
            # This is an invalid slug choice, so the default queryset is returned
            lambda self: (
                self.user,
                self.organization,
                self.team_empty,
                [self.project],
            ),
            lambda self: (self.owner, self.organization, self.team_empty, []),
        ],
    )
    def test_filtered_queryset_team_choice(self, get_params):
        """Valid team choice returns expected results."""
        (user, organization, team, projects) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            {"teams__slug": team.slug},
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            projects,
            transform=lambda o: o,
            ordered=False,
        )

    def test_filtered_queryset_team_invalid_choice(self):
        """Invalid team choice returns the original queryset."""
        filter = self.get_filterset_for_user(
            self.user,
            {"teams__slug": self.other_team.slug},
            organization=self.organization,
        )
        assertQuerySetEqual(
            filter.qs,
            [self.project],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, ["", self.project.slug]),
            lambda self: (self.owner, self.organization, ["", self.project.slug]),
            lambda self: (
                self.other_user,
                self.other_organization,
                ["", self.other_project.slug],
            ),
            lambda self: (
                self.other_owner,
                self.other_organization,
                ["", self.other_project.slug],
            ),
        ],
    )
    def test_project_filter_choices(self, get_params):
        """Project filter choices limited to organization projects."""
        (user, organization, projects) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            organization=organization,
        )
        assert list(dict(filter.filters["slug"].field.choices).keys()) == projects

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, ["", self.team.slug]),
            lambda self: (
                self.owner,
                self.organization,
                ["", self.team.slug, self.team_empty.slug],
            ),
            lambda self: (
                self.other_user,
                self.other_organization,
                ["", self.other_team.slug],
            ),
            lambda self: (
                self.other_owner,
                self.other_organization,
                ["", self.other_team.slug],
            ),
        ],
    )
    def test_team_filter_choices(self, get_params):
        """Team filter choices limited to organization teams."""
        (user, organization, teams) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            organization=organization,
        )
        assert list(dict(filter.filters["teams__slug"].field.choices).keys()) == teams


class TestOrganizationTeamListFilterSet(OrganizationFilterTestCase):
    def get_filterset_for_user(self, user, *args, **kwargs):
        request = RequestFactory().get("")
        request.user = user
        queryset = Team.objects.member(user).filter(
            organization=kwargs.get("organization", self.organization),
        )
        kwargs.update(
            {
                "queryset": queryset,
                "request": request,
            }
        )
        return OrganizationTeamListFilterSet(*args, **kwargs)

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, [self.team]),
            lambda self: (
                self.owner,
                self.organization,
                [self.team, self.team_empty],
            ),
            lambda self: (
                self.other_user,
                self.other_organization,
                [self.other_team],
            ),
            lambda self: (
                self.other_owner,
                self.other_organization,
                [self.other_team],
            ),
        ],
    )
    def test_unfiltered_queryset(self, get_params):
        """No active filters returns full queryset."""
        (user, organization, teams) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            teams,
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, self.team),
            lambda self: (self.owner, self.organization, self.team_empty),
            lambda self: (self.other_user, self.other_organization, self.other_team),
            lambda self: (self.other_owner, self.other_organization, self.other_team),
        ],
    )
    def test_filtered_queryset_team_choice(self, get_params):
        """Valid team choice returns expected results."""
        (user, organization, team) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            {"slug": team.slug},
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            [team],
            transform=lambda o: o,
            ordered=False,
        )

    def test_filtered_queryset_team_invalid_choice(self):
        """Invalid team choice returns the original queryset."""
        filter = self.get_filterset_for_user(
            self.user,
            {"slug": self.other_team.slug},
            organization=self.organization,
        )
        assertQuerySetEqual(
            filter.qs,
            [self.team],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, ["", self.team.slug]),
            lambda self: (
                self.owner,
                self.organization,
                ["", self.team.slug, self.team_empty.slug],
            ),
            lambda self: (
                self.other_user,
                self.other_organization,
                ["", self.other_team.slug],
            ),
            lambda self: (
                self.other_owner,
                self.other_organization,
                ["", self.other_team.slug],
            ),
        ],
    )
    def test_team_filter_choices(self, get_params):
        """Team filter choices limited to organization teams."""
        (user, organization, teams) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            organization=organization,
        )
        assert list(dict(filter.filters["slug"].field.choices).keys()) == teams


class TestOrganizationTeamMemberFilterSet(OrganizationFilterTestCase):
    def get_filterset_for_user(self, user, *args, **kwargs):
        request = RequestFactory().get("")
        request.user = user
        organization = kwargs.get("organization", self.organization)
        queryset = organization.members
        kwargs.update(
            {
                "queryset": queryset,
                "request": request,
            }
        )
        return OrganizationTeamMemberListFilterSet(*args, **kwargs)

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, [self.user, self.owner]),
            lambda self: (self.owner, self.organization, [self.user, self.owner]),
            lambda self: (
                self.other_user,
                self.other_organization,
                [self.other_user, self.other_owner],
            ),
            lambda self: (
                self.other_owner,
                self.other_organization,
                [self.other_user, self.other_owner],
            ),
        ],
    )
    def test_unfiltered_queryset(self, get_params):
        """No active filters returns full queryset."""
        (user, organization, members) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            members,
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, self.team, [self.user]),
            lambda self: (self.owner, self.organization, self.team, [self.user]),
            lambda self: (self.owner, self.organization, self.team_empty, []),
        ],
    )
    def test_filtered_queryset_team_choice(self, get_params):
        """Valid team choice returns expected results."""
        (user, organization, team, members) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            {"teams__slug": team.slug},
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            members,
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, "readonly", []),
            lambda self: (self.user, self.organization, "admin", [self.user]),
            lambda self: (self.user, self.organization, "owner", [self.owner]),
        ],
    )
    def test_filtered_queryset_access_choice(self, get_params):
        """Valid access choice returns expected results."""
        (user, organization, access, members) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            {"access": access},
            organization=organization,
        )
        assertQuerySetEqual(
            filter.qs,
            members,
            transform=lambda o: o,
            ordered=False,
        )

    def test_filtered_queryset_team_invalid_choice(self):
        """Invalid team choice returns the original queryset."""
        filter = self.get_filterset_for_user(
            self.user,
            {"teams__slug": self.other_team.slug},
            organization=self.organization,
        )
        assertQuerySetEqual(
            filter.qs,
            [self.owner, self.user],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "get_params",
        [
            lambda self: (self.user, self.organization, ["", self.team.slug]),
            lambda self: (
                self.owner,
                self.organization,
                ["", self.team.slug, self.team_empty.slug],
            ),
            lambda self: (
                self.other_user,
                self.other_organization,
                ["", self.other_team.slug],
            ),
            lambda self: (
                self.other_owner,
                self.other_organization,
                ["", self.other_team.slug],
            ),
        ],
    )
    def test_team_filter_choices(self, get_params):
        """Team filter choices limited to organization teams with permisisons."""
        (user, organization, choices) = get_params(self)
        filter = self.get_filterset_for_user(
            user,
            organization=organization,
        )
        assert list(dict(filter.filters["teams__slug"].field.choices).keys()) == choices

    def test_access_filter_choices(self):
        """Access filter choices are correct."""
        filter = self.get_filterset_for_user(
            self.user,
            organization=self.organization,
        )
        assert list(dict(filter.filters["access"].field.choices).keys()) == [
            "",
            "readonly",
            "admin",
            "owner",
        ]
