# -*- coding: utf-8 -*-
import django_dynamic_fixture
import pytest

from django.contrib.auth.models import User

from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestProjectOrganizationSignal:

    def test_project_get_deleted_upon_user_delete(self):
        """If the user has Project where he is the only
        user, upon deleting his account, the Project
        should also get deleted."""

        project = django_dynamic_fixture.get(Project)
        user1 = django_dynamic_fixture.get(User)
        project.users.add(user1)

        project.refresh_from_db()
        assert project.users.all().count() == 1

        # Delete the user
        user1.delete()
        # The object should not exist
        project = Project.objects.all().filter(id=project.id)
        assert not project.exists()

    def test_multiple_users_project_not_delete(self):
        """Check Project which have multiple users do not
        get deleted when any of the user delete his account."""

        project = django_dynamic_fixture.get(Project)
        user1 = django_dynamic_fixture.get(User)
        user2 = django_dynamic_fixture.get(User)
        project.users.add(user1, user2)

        project.refresh_from_db()
        assert project.users.all().count() > 1
        # Delete 1 user of the project
        user1.delete()

        # The project should still exist and it should have 1 user
        project.refresh_from_db()
        assert project.id
        obj_users = project.users.all()
        assert len(obj_users) == 1
        assert user2 in obj_users
