import pytest
import django_dynamic_fixture

from django.contrib.auth.models import User

from readthedocs.oauth.models import RemoteOrganization
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestProjectOrganizationSignal(object):

    @pytest.mark.parametrize('model_class', [Project, RemoteOrganization])
    def test_project_organization_get_deleted_upon_user_delete(self, model_class):
        """
        If the user has Project or RemoteOrganization where he is the only user,
        upon deleting his account, the Project or RemoteOrganization should also get
        deleted.
        """

        obj = django_dynamic_fixture.get(model_class)
        user1 = django_dynamic_fixture.get(User)
        obj.users.add(user1)

        obj.refresh_from_db()
        assert obj.users.all().count() == 1

        # Delete the user
        user1.delete()
        # The object should not exist
        obj = model_class.objects.all().filter(id=obj.id)
        assert not obj.exists()

    @pytest.mark.parametrize('model_class', [Project, RemoteOrganization])
    def test_multiple_users_project_organization_not_delete(self, model_class):
        """
        Check Project or RemoteOrganization which have multiple users do not get deleted
        when any of the user delete his account.
        """

        obj = django_dynamic_fixture.get(model_class)
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
