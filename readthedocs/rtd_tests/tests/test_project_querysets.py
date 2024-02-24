from datetime import timedelta

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import Feature, Project
from readthedocs.projects.querysets import (
    ChildRelatedProjectQuerySet,
    ParentRelatedProjectQuerySet,
)


class ProjectQuerySetTests(TestCase):
    def setUp(self):
        self.user = get(User)
        self.another_user = get(User)

        self.project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.user],
            main_language_project=None,
        )
        self.project_private = get(
            Project,
            privacy_level=PRIVATE,
            users=[self.user],
            main_language_project=None,
        )

        self.another_project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.another_user],
            main_language_project=None,
        )
        self.another_project_private = get(
            Project,
            privacy_level=PRIVATE,
            users=[self.another_user],
            main_language_project=None,
        )

        self.shared_project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.user, self.another_user],
            main_language_project=None,
        )
        self.shared_project_private = get(
            Project,
            privacy_level=PRIVATE,
            users=[self.user, self.another_user],
            main_language_project=None,
        )

        self.user_projects = {
            self.project,
            self.project_private,
            self.shared_project,
            self.shared_project_private,
        }

        self.another_user_projects = {
            self.another_project,
            self.another_project_private,
            self.shared_project,
            self.shared_project_private,
        }

    def test_subproject_queryset_attributes(self):
        self.assertEqual(ParentRelatedProjectQuerySet.project_field, "parent")
        self.assertTrue(ParentRelatedProjectQuerySet.use_for_related_fields)
        self.assertEqual(ChildRelatedProjectQuerySet.project_field, "child")
        self.assertTrue(ChildRelatedProjectQuerySet.use_for_related_fields)

    def test_subproject_queryset_as_manager_gets_correct_class(self):
        mgr = ChildRelatedProjectQuerySet.as_manager()
        self.assertEqual(
            mgr.__class__.__name__,
            "ManagerFromChildRelatedProjectQuerySet",
        )
        mgr = ParentRelatedProjectQuerySet.as_manager()
        self.assertEqual(
            mgr.__class__.__name__,
            "ManagerFromParentRelatedProjectQuerySet",
        )

    def test_is_active(self):
        project = get(Project, skip=False)
        self.assertTrue(Project.objects.is_active(project))

        project = get(Project, skip=True)
        self.assertFalse(Project.objects.is_active(project))

        user = get(User)
        user.profile.banned = True
        user.profile.save()
        project = fixture.get(Project, skip=False, users=[user])
        self.assertFalse(Project.objects.is_active(project))

        user.profile.banned = False
        user.profile.save()
        self.assertTrue(Project.objects.is_active(project))

        organization = get(Organization, disabled=False)
        organization.projects.add(project)
        self.assertTrue(Project.objects.is_active(project))

        organization.disabled = True
        organization.save()
        self.assertFalse(Project.objects.is_active(project))

    def test_dashboard(self):
        query = Project.objects.dashboard(user=self.user)
        self.assertEqual(query.count(), len(self.user_projects))
        self.assertEqual(set(query), self.user_projects)

        query = Project.objects.dashboard(user=self.another_user)
        self.assertEqual(query.count(), len(self.another_user_projects))
        self.assertEqual(set(query), self.another_user_projects)

    def test_public(self):
        query = Project.objects.public()
        projects = {
            self.project,
            self.another_project,
            self.shared_project,
        }
        self.assertEqual(query.count(), len(projects))
        self.assertEqual(set(query), projects)

    def test_public_user(self):
        query = Project.objects.public(user=self.user)
        projects = self.user_projects | {self.another_project}
        self.assertEqual(query.count(), len(projects))
        self.assertEqual(set(query), projects)

        query = Project.objects.public(user=self.another_user)
        projects = self.another_user_projects | {self.project}
        self.assertEqual(query.count(), len(projects))
        self.assertEqual(set(query), projects)

    def test_for_user(self):
        query = Project.objects.for_user(user=self.user)
        projects = self.user_projects
        self.assertEqual(query.count(), len(projects))
        self.assertEqual(set(query), projects)

        query = Project.objects.for_user(user=self.another_user)
        projects = self.another_user_projects
        self.assertEqual(query.count(), len(projects))
        self.assertEqual(set(query), projects)

    def test_for_user_and_viewer(self):
        query = Project.objects.for_user_and_viewer(
            user=self.user,
            viewer=self.another_user,
        )
        projects = {
            self.shared_project,
            self.shared_project_private,
            self.project,
        }
        self.assertEqual(query.count(), len(projects))
        self.assertEqual(set(query), projects)

        # Now `self.user` is the viewer.
        query = Project.objects.for_user_and_viewer(
            user=self.another_user,
            viewer=self.user,
        )
        projects = {
            self.shared_project,
            self.shared_project_private,
            self.another_project,
        }
        self.assertEqual(query.count(), len(projects))
        self.assertEqual(set(query), projects)

    def test_for_user_and_viewer_same_user(self):
        query = Project.objects.for_user_and_viewer(user=self.user, viewer=self.user)
        projects = self.user_projects
        self.assertEqual(query.count(), len(projects))
        self.assertEqual(set(query), projects)

    def test_only_owner(self):
        user = get(User)
        another_user = get(User)

        project_one = get(Project, slug="one", users=[user])
        project_two = get(Project, slug="two", users=[user])
        project_three = get(Project, slug="three", users=[another_user])
        get(Project, slug="four", users=[user, another_user])
        get(Project, slug="five", users=[])

        project_with_organization = get(Project, slug="six", users=[user])
        get(Organization, owners=[user], projects=[project_with_organization])

        self.assertEqual(
            {project_one, project_two}, set(Project.objects.single_owner(user))
        )
        self.assertEqual(
            {project_three}, set(Project.objects.single_owner(another_user))
        )


class FeatureQuerySetTests(TestCase):
    def test_feature_for_project_is_explicit_applied(self):
        project = fixture.get(Project, main_language_project=None)
        feature = fixture.get(Feature, projects=[project])
        self.assertTrue(project.has_feature(feature.feature_id))

    def test_feature_for_project_is_implicitly_applied(self):
        project = fixture.get(Project, main_language_project=None)
        # Explicit feature
        feature1 = fixture.get(Feature, projects=[project])
        # False implicit feature
        feature2 = fixture.get(
            Feature,
            projects=[],
            add_date=project.pub_date + timedelta(days=1),
            default_true=False,
        )
        # True implicit feature before add date
        feature3 = fixture.get(
            Feature,
            projects=[],
            add_date=project.pub_date + timedelta(days=1),
            default_true=True,
        )
        # True implicit feature after add date
        feature4 = fixture.get(
            Feature,
            projects=[],
            add_date=project.pub_date - timedelta(days=1),
            default_true=True,
        )
        self.assertQuerySetEqual(
            Feature.objects.for_project(project),
            [feature1, feature3],
            ordered=False,
        )

    def test_feature_future_default_true(self):
        project = fixture.get(Project, main_language_project=None)
        # Explicit feature
        feature1 = fixture.get(Feature, projects=[project])

        # False implicit feature
        feature2 = fixture.get(
            Feature,
            projects=[],
            add_date=project.pub_date + timedelta(days=1),
            future_default_true=False,
        )

        # True implicit feature after add date
        feature3 = fixture.get(
            Feature,
            projects=[],
            add_date=project.pub_date - timedelta(days=1),
            future_default_true=True,
        )
        self.assertQuerySetEqual(
            Feature.objects.for_project(project),
            [feature1, feature3],
            ordered=False,
        )

    def test_feature_multiple_projects(self):
        project1 = fixture.get(Project, main_language_project=None)
        project2 = fixture.get(Project, main_language_project=None)
        feature = fixture.get(Feature, projects=[project1, project2])
        self.assertQuerySetEqual(
            Feature.objects.for_project(project1),
            [feature],
            ordered=False,
        )
