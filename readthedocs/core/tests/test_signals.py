# -*- coding: utf-8 -*-
import django_dynamic_fixture
import pytest
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User

from readthedocs.oauth.models import (
    RemoteOrganization,
    RemoteOrganizationRelation,
)
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestProjectOrganizationSignal:

    def test_project_get_deleted_upon_user_delete(self):
        """If the user has Project where he is the only
        user, upon deleting his account, the Project
        should also get deleted."""

        obj = django_dynamic_fixture.get(Project)
        user1 = django_dynamic_fixture.get(User)
        obj.users.add(user1)

        obj.refresh_from_db()
        assert obj.users.all().count() == 1

        # Delete the user
        user1.delete()
        # The object should not exist
        obj = Project.objects.all().filter(id=obj.id)
        assert not obj.exists()

    def test_organization_get_deleted_upon_user_delete(self):
        """If the user has RemoteOrganization where he is the only
        user, upon deleting his account, the RemoteOrganization
        should also get deleted."""
        user1 = django_dynamic_fixture.get(User)
        account = django_dynamic_fixture.get(SocialAccount, user=user1)
        obj = django_dynamic_fixture.get(RemoteOrganization)

        django_dynamic_fixture.get(
            RemoteOrganizationRelation,
            remote_organization=obj,
            user=user1,
            account=account
        )

        obj.refresh_from_db()
        assert obj.users.all().count() == 1

        # Delete the user
        user1.delete()
        # The object should not exist
        obj = RemoteOrganization.objects.all().filter(id=obj.id)
        assert not obj.exists()

    def test_multiple_users_project_not_delete(self):
        """Check Project or RemoteOrganization which have multiple users do not
        get deleted when any of the user delete his account."""

        obj = django_dynamic_fixture.get(Project)
        user1 = django_dynamic_fixture.get(User)
        user2 = django_dynamic_fixture.get(User)
        obj.users.add(user1, user2)

        obj.refresh_from_db()
        assert obj.users.all().count() > 1
        # Delete 1 user of the project
        user1.delete()

        # The project should still exist and it should have 1 user
        obj.refresh_from_db()
        assert obj.id
        obj_users = obj.users.all()
        assert len(obj_users) == 1
        assert user2 in obj_users

    def test_multiple_users_organization_not_delete(self):
        """Check RemoteOrganization which have multiple users do not
        get deleted when any of the user delete his account."""
        user1 = django_dynamic_fixture.get(User)
        user2 = django_dynamic_fixture.get(User)
        account1 = django_dynamic_fixture.get(SocialAccount, user=user1)
        account2 = django_dynamic_fixture.get(SocialAccount, user=user2)

        obj = django_dynamic_fixture.get(RemoteOrganization)

        django_dynamic_fixture.get(
            RemoteOrganizationRelation,
            remote_organization=obj,
            user=user1,
            account=account1
        )
        django_dynamic_fixture.get(
            RemoteOrganizationRelation,
            remote_organization=obj,
            user=user2,
            account=account2
        )

        obj.refresh_from_db()
        assert obj.users.all().count() > 1
        # Delete 1 user of the project
        user1.delete()

        # The project should still exist and it should have 1 user
        obj.refresh_from_db()
        assert obj.id
        obj_users = obj.users.all()
        assert len(obj_users) == 1
        assert user2 in obj_users
