from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.projects.models import Project
from readthedocs.projects.utils import get_projects_only_owner


class TestUtils(TestCase):

    def test_get_projects_only_owner(self):
        user = get(User)
        another_user = get(User)

        project_one = get(
            Project,
            slug='one',
            users=[user],
            main_language_project=None,
        )
        project_two = get(
            Project,
            slug='two',
            users=[user],
            main_language_project=None,
        )
        project_three = get(
            Project,
            slug='three',
            users=[another_user],
            main_language_project=None,
        )
        project_four = get(
            Project,
            slug='four',
            users=[user, another_user],
            main_language_project=None,
        )

        project_five = get(
            Project,
            slug='five',
            users=[],
            main_language_project=None,
        )

        expected = {project_one, project_two}
        self.assertEqual(expected, set(get_projects_only_owner(user)))
