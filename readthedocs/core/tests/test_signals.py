import pytest
from django.contrib.auth.models import User
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.organizations.models import Organization, Team, TeamMember
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestProjectOrganizationSignal:
    def test_delete_user_deletes_projects(self):
        """When deleting a user, delete projects where it's the only owner."""
        user = get(User)
        another_user = get(User)
        project_one = get(Project, slug="one", users=[user])
        project_two = get(Project, slug="two", users=[user])
        project_three = get(Project, slug="three", users=[another_user])
        project_four = get(Project, slug="four", users=[user, another_user])

        project_five = get(
            Project,
            slug="five",
            users=[],
        )
        assert Project.objects.all().count() == 5
        assert Version.objects.all().count() == 5

        user.delete()
        assert {project_three, project_four, project_five} == set(Project.objects.all())
        assert Version.objects.all().count() == 3

    def test_delete_user_deletes_organizations(self):
        """When deleting a user, delete organizations where it's the only owner."""
        user = get(User)
        member = get(User)
        another_user = get(User)
        project_one = get(Project, slug="one")
        project_two = get(Project, slug="two")
        project_three = get(Project, slug="three")
        org_one = get(Organization, slug="one", owners=[user], projects=[project_one])
        org_two = get(
            Organization,
            slug="two",
            owners=[user, another_user],
            projects=[project_two],
        )
        org_three = get(
            Organization, slug="three", owners=[another_user], projects=[project_three]
        )

        team_one = get(
            Team, organization=org_one, members=[member, user], projects=[project_one]
        )
        team_two = get(
            Team,
            organization=org_three,
            members=[another_user],
            projects=[project_three],
        )

        assert Organization.objects.all().count() == 3
        assert Project.objects.all().count() == 3
        assert Version.objects.all().count() == 3
        assert Team.objects.all().count() == 2
        assert TeamMember.objects.all().count() == 3
        assert User.objects.all().count() == 3

        user.delete()

        assert {org_two, org_three} == set(Organization.objects.all())
        assert {project_two, project_three} == set(Project.objects.all())
        assert Version.objects.all().count() == 2
        assert {team_two} == set(Team.objects.all())
        assert TeamMember.objects.all().count() == 1
        assert User.objects.all().count() == 2
