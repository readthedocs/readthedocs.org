from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization


class TestOrganizationQuerysets(TestCase):
    def test_only_owner(self):
        user = get(User)
        another_user = get(User)

        org_one = get(Organization, slug="one", owners=[user])
        org_two = get(Organization, slug="two", owners=[user])
        org_three = get(Organization, slug="three", owners=[another_user])
        get(Organization, slug="four", owners=[user, another_user])
        get(Organization, slug="five", owners=[])

        self.assertEqual(
            {org_one, org_two}, set(Organization.objects.single_owner(user))
        )
        self.assertEqual(
            {org_three}, set(Organization.objects.single_owner(another_user))
        )
