import django_dynamic_fixture as fixture
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from pytest_django.asserts import assertQuerySetEqual

from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project


@pytest.mark.django_db
class OrganizationFilterTestCase:
    @pytest.fixture(autouse=True)
    def set_up(self, settings, client):
        settings.RTD_ALLOW_ORGANIZATIONS = True
        self.client = client


@pytest.fixture
def filter_data(request):
    users = dict(
        user_a=fixture.get(User),
        owner_a=fixture.get(User),
        user_b=fixture.get(User),
        owner_b=fixture.get(User),
    )

    projects = dict(
        project_a=fixture.get(Project),
        project_b=fixture.get(Project),
    )

    organizations = dict(
        org_a=fixture.get(
            Organization,
            owners=[users["owner_a"]],
            projects=[projects["project_a"]],
        ),
        org_b=fixture.get(
            Organization,
            owners=[users["owner_b"]],
            projects=[projects["project_b"]],
        ),
    )

    teams = dict(
        team_a=fixture.get(
            Team,
            access="admin",
            organization=organizations["org_a"],
            members=[users["user_a"]],
            projects=[projects["project_a"]],
        ),
        team_a_empty=fixture.get(
            Team,
            access="readonly",
            organization=organizations["org_a"],
            members=[],
            projects=[],
        ),
        team_b=fixture.get(
            Team,
            access="admin",
            organization=organizations["org_b"],
            members=[users["user_b"]],
            projects=[projects["project_b"]],
        ),
    )

    return dict(
        users=users,
        projects=projects,
        organizations=organizations,
        teams=teams,
    )


@pytest.fixture
def user(request, filter_data):
    return filter_data["users"][request.param]


@pytest.fixture
def organization(request, filter_data):
    return filter_data["organizations"][request.param]


@pytest.fixture
def team(request, filter_data):
    return filter_data["teams"][request.param]


@pytest.fixture
def teams(request, filter_data):
    return [filter_data["teams"][key] for key in request.param]


@pytest.fixture
def project(request, filter_data):
    return filter_data["projects"][request.param]


@pytest.fixture
def users(request, filter_data):
    return [filter_data["users"][key] for key in request.param]


@pytest.mark.parametrize(
    "user,organization",
    [
        ("user_a", "org_a"),
        ("owner_a", "org_a"),
        ("user_b", "org_b"),
        ("owner_b", "org_b"),
    ],
    indirect=True,
)
class TestOrganizationFilterSet(OrganizationFilterTestCase):
    def get_filterset_for_user(self, user, organization, data=None, **kwargs):
        self.client.force_login(user)
        url = reverse("organization_list")
        resp = self.client.get(url, data=data)
        return resp.context_data.get("filter")

    def test_unfiltered_queryset(self, user, organization):
        """No active filters returns full queryset."""
        filter = self.get_filterset_for_user(user, organization)
        assertQuerySetEqual(
            filter.qs,
            [organization],
            transform=lambda o: o,
            ordered=False,
        )

    def test_filtered_queryset_choice(self, user, organization):
        """Valid project choice returns expected results."""
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"slug": organization.slug},
        )
        assert filter.is_valid()
        assertQuerySetEqual(
            filter.qs,
            [organization],
            transform=lambda o: o,
            ordered=False,
        )

    def test_filtered_queryset_invalid_choice(self, user, organization):
        """Invalid project choice returns the original queryset."""
        wrong_organization = fixture.get(
            Organization,
            owners=[],
            projects=[],
            teams=[],
        )
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"slug": wrong_organization.slug},
        )
        assert not filter.is_valid()
        # Validation will fail, but the full queryset is still returned. This is
        # handled differently at the view level however.
        assertQuerySetEqual(
            filter.qs,
            [organization],
            transform=lambda o: o,
            ordered=False,
        )

    def test_organization_filter_choices(self, user, organization):
        filter = self.get_filterset_for_user(
            user,
            organization,
        )
        assert list(dict(filter.filters["slug"].field.choices).keys()) == [
            "",
            organization.slug,
        ]


class TestOrganizationProjectFilterSet(OrganizationFilterTestCase):
    def get_filterset_for_user(self, user, organization, data=None, **kwargs):
        self.client.force_login(user)
        url = reverse("organization_detail", kwargs={"slug": organization.slug})
        resp = self.client.get(url, data=data)
        return resp.context_data.get("filter")

    @pytest.mark.parametrize(
        "user,organization,project",
        [
            ("user_a", "org_a", "project_a"),
            ("owner_a", "org_a", "project_a"),
            ("user_b", "org_b", "project_b"),
            ("owner_b", "org_b", "project_b"),
        ],
        indirect=True,
    )
    def test_unfiltered_queryset(self, user, organization, project):
        """No active filters returns full queryset."""
        filter = self.get_filterset_for_user(user, organization)
        assertQuerySetEqual(
            filter.qs,
            [project],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,project",
        [
            ("user_a", "org_a", "project_a"),
            ("owner_a", "org_a", "project_a"),
            ("user_b", "org_b", "project_b"),
            ("owner_b", "org_b", "project_b"),
        ],
        indirect=True,
    )
    def test_filtered_queryset_project_choice(self, user, organization, project):
        """Valid project choice returns expected results."""
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"slug": project.slug},
        )
        assertQuerySetEqual(
            filter.qs,
            [project],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,project",
        [
            ("user_a", "org_a", "project_a"),
            ("owner_a", "org_a", "project_a"),
            ("user_b", "org_b", "project_b"),
            ("owner_b", "org_b", "project_b"),
        ],
        indirect=True,
    )
    def test_filtered_queryset_project_invalid_choice(
        self, user, organization, project
    ):
        """Invalid project choice returns the original queryset."""
        wrong_project = fixture.get(Project)
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"slug": wrong_project.slug},
        )
        assert not filter.is_valid()
        # The full queryset is still returned when a filterset is invalid
        assertQuerySetEqual(
            filter.qs,
            [project],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,team,projects",
        [
            ("user_a", "org_a", "team_a", ["project_a"]),
            ("owner_a", "org_a", "team_a", ["project_a"]),
            ("user_a", "org_a", "team_a_empty", ["project_a"]),
            ("owner_a", "org_a", "team_a_empty", []),
            ("user_b", "org_b", "team_b", ["project_b"]),
            ("owner_b", "org_b", "team_b", ["project_b"]),
        ],
        indirect=["user", "organization", "team"],
    )
    def test_filtered_queryset_team_choice(
        self, user, organization, team, projects, filter_data
    ):
        """Valid team choice returns expected results."""
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"teams__slug": team.slug},
        )
        assertQuerySetEqual(
            filter.qs,
            [filter_data["projects"][key] for key in projects],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,project",
        [
            ("user_a", "org_a", "project_a"),
            ("owner_a", "org_a", "project_a"),
            ("user_b", "org_b", "project_b"),
            ("owner_b", "org_b", "project_b"),
        ],
        indirect=True,
    )
    def test_filtered_queryset_team_invalid_choice(self, user, organization, project):
        """Invalid team choice returns the original queryset."""
        wrong_team = fixture.get(Team)
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"teams__slug": wrong_team.slug},
        )
        assert not filter.is_valid()
        # By default, invalid filtersets return the original queryset
        assertQuerySetEqual(
            filter.qs,
            [project],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,project",
        [
            ("user_a", "org_a", "project_a"),
            ("owner_a", "org_a", "project_a"),
            ("user_b", "org_b", "project_b"),
            ("owner_b", "org_b", "project_b"),
        ],
        indirect=True,
    )
    def test_project_filter_choices(self, user, organization, project):
        """Project filter choices limited to organization projects."""
        filter = self.get_filterset_for_user(
            user,
            organization,
        )
        assert list(dict(filter.filters["slug"].field.choices).keys()) == [
            "",
            project.slug,
        ]

    @pytest.mark.parametrize(
        "user,organization,teams",
        [
            ("user_a", "org_a", ["team_a"]),
            ("owner_a", "org_a", ["team_a", "team_a_empty"]),
            ("user_b", "org_b", ["team_b"]),
            ("owner_b", "org_b", ["team_b"]),
        ],
        indirect=["user", "organization"],
    )
    def test_team_filter_choices(self, user, organization, teams, filter_data):
        """Team filter choices limited to organization teams."""
        filter = self.get_filterset_for_user(
            user,
            organization,
        )
        choices = [filter_data["teams"][key].slug for key in teams]
        choices.insert(0, "")
        assert list(dict(filter.filters["teams__slug"].field.choices).keys()) == choices


class TestOrganizationTeamListFilterSet(OrganizationFilterTestCase):
    def get_filterset_for_user(self, user, organization, data=None, **kwargs):
        self.client.force_login(user)
        url = reverse("organization_team_list", kwargs={"slug": organization.slug})
        resp = self.client.get(url, data=data)
        return resp.context_data.get("filter")

    @pytest.mark.parametrize(
        "user,organization,teams",
        [
            ("user_a", "org_a", ["team_a"]),
            ("owner_a", "org_a", ["team_a", "team_a_empty"]),
            ("user_b", "org_b", ["team_b"]),
            ("owner_b", "org_b", ["team_b"]),
        ],
        indirect=True,
    )
    def test_unfiltered_queryset(self, user, organization, teams):
        """No active filters returns full queryset."""
        filter = self.get_filterset_for_user(
            user,
            organization,
        )
        assertQuerySetEqual(
            filter.qs,
            teams,
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,team",
        [
            ("user_a", "org_a", "team_a"),
            ("owner_a", "org_a", "team_a"),
            ("owner_a", "org_a", "team_a_empty"),
            ("user_b", "org_b", "team_b"),
            ("owner_b", "org_b", "team_b"),
        ],
        indirect=True,
    )
    def test_filtered_queryset_team_choice(self, user, organization, team):
        """Valid team choice returns expected results."""
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"slug": team.slug},
        )
        assertQuerySetEqual(
            filter.qs,
            [team],
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,team",
        [
            ("user_a", "org_a", "team_a"),
            ("owner_a", "org_a", "team_a"),
            ("user_b", "org_b", "team_b"),
            ("owner_b", "org_b", "team_b"),
        ],
        indirect=True,
    )
    def test_filtered_queryset_team_invalid_choice(self, user, organization, team):
        """Invalid team choice returns the original queryset."""
        wrong_team = fixture.get(Team)
        filter = self.get_filterset_for_user(
            user,
            organization,
            {"slug": wrong_team.slug},
        )
        assert not filter.is_valid()

    @pytest.mark.parametrize(
        "user,organization,teams",
        [
            ("user_a", "org_a", ["team_a"]),
            ("owner_a", "org_a", ["team_a", "team_a_empty"]),
            ("user_b", "org_b", ["team_b"]),
            ("owner_b", "org_b", ["team_b"]),
        ],
        indirect=True,
    )
    def test_team_filter_choices(self, user, organization, teams):
        """Team filter choices limited to organization teams."""
        filter = self.get_filterset_for_user(
            user,
            organization,
        )
        choices = [team.slug for team in teams]
        choices.insert(0, "")
        assert list(dict(filter.filters["slug"].field.choices).keys()) == choices


class TestOrganizationTeamMemberFilterSet(OrganizationFilterTestCase):
    def get_filterset_for_user(self, user, organization, data=None, **kwargs):
        self.client.force_login(user)
        url = reverse("organization_members", kwargs={"slug": organization.slug})
        resp = self.client.get(url, data=data)
        return resp.context_data.get("filter")

    @pytest.mark.parametrize(
        "user,organization,users",
        [
            ("user_a", "org_a", ["user_a", "owner_a"]),
            ("owner_a", "org_a", ["user_a", "owner_a"]),
            ("user_b", "org_b", ["user_b", "owner_b"]),
            ("owner_b", "org_b", ["user_b", "owner_b"]),
        ],
        indirect=True,
    )
    def test_unfiltered_queryset(self, user, organization, users):
        """No active filters returns full queryset."""
        filter = self.get_filterset_for_user(
            user,
            organization,
        )
        assertQuerySetEqual(
            filter.qs,
            users,
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,team,users",
        [
            ("user_a", "org_a", "team_a", ["user_a"]),
            ("owner_a", "org_a", "team_a", ["user_a"]),
            ("owner_a", "org_a", "team_a_empty", []),
            ("user_b", "org_b", "team_b", ["user_b"]),
            ("owner_b", "org_b", "team_b", ["user_b"]),
        ],
        indirect=True,
    )
    def test_filtered_queryset_team_choice(self, user, organization, team, users):
        """Valid team choice returns expected results."""
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"teams__slug": team.slug},
        )
        assertQuerySetEqual(
            filter.qs,
            users,
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization,access,users",
        [
            ("user_a", "org_a", "readonly", []),
            ("user_a", "org_a", "admin", ["user_a"]),
            ("user_a", "org_a", "owner", ["owner_a"]),
            ("owner_a", "org_a", "readonly", []),
            ("owner_a", "org_a", "admin", ["user_a"]),
            ("owner_a", "org_a", "owner", ["owner_a"]),
        ],
        indirect=["user", "organization", "users"],
    )
    def test_filtered_queryset_access_choice(self, user, organization, access, users):
        """Valid access choice returns expected results."""
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"access": access},
        )
        assertQuerySetEqual(
            filter.qs,
            users,
            transform=lambda o: o,
            ordered=False,
        )

    @pytest.mark.parametrize(
        "user,organization",
        [
            ("user_a", "org_a"),
            ("owner_a", "org_a"),
            ("user_b", "org_b"),
            ("owner_b", "org_b"),
        ],
        indirect=True,
    )
    def test_filtered_queryset_team_invalid_choice(self, user, organization):
        """Invalid team choice returns the original queryset."""
        wrong_team = fixture.get(Team)
        filter = self.get_filterset_for_user(
            user,
            organization,
            data={"teams__slug": wrong_team.slug},
        )
        assert not filter.is_valid()

    @pytest.mark.parametrize(
        "user,organization,teams",
        [
            ("user_a", "org_a", ["team_a"]),
            ("owner_a", "org_a", ["team_a", "team_a_empty"]),
            ("user_b", "org_b", ["team_b"]),
            ("owner_b", "org_b", ["team_b"]),
        ],
        indirect=True,
    )
    def test_team_filter_choices(self, user, organization, teams):
        """Team filter choices limited to organization teams with permisisons."""
        filter = self.get_filterset_for_user(
            user,
            organization=organization,
        )
        choices = [team.slug for team in teams]
        choices.insert(0, "")
        assert list(dict(filter.filters["teams__slug"].field.choices).keys()) == choices

    @pytest.mark.parametrize(
        "user,organization",
        [
            ("user_a", "org_a"),
            ("owner_a", "org_a"),
            ("user_b", "org_b"),
            ("owner_b", "org_b"),
        ],
        indirect=True,
    )
    def test_access_filter_choices(self, user, organization):
        """Access filter choices are correct."""
        filter = self.get_filterset_for_user(
            user,
            organization,
        )
        assert list(dict(filter.filters["access"].field.choices).keys()) == [
            "",
            "readonly",
            "admin",
            "owner",
        ]
