import pytest

from django.contrib.auth.models import User
from django_dynamic_fixture import G

from readthedocs.oauth.models import RemoteOrganization
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestProjectOrganizationSignal(object):

    @pytest.mark.parametrize('model', [Project, RemoteOrganization])
    def test_multiple_users_project_organization_not_delete(self, model):
        """
        Check Project or RemoteOrganization which have multiple users do not get deleted
        when any of the user delete his account.
        """

        obj = G(model)
        user1 = G(User)
        user2 = G(User)
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
