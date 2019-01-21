# -*- coding: utf-8 -*-
from datetime import timedelta

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.projects.models import Feature, Project
from readthedocs.projects.querysets import (
    ChildRelatedProjectQuerySet,
    ParentRelatedProjectQuerySet,
)


class ProjectQuerySetTests(TestCase):

    def test_subproject_queryset_attributes(self):
        self.assertEqual(ParentRelatedProjectQuerySet.project_field, 'parent')
        self.assertTrue(ParentRelatedProjectQuerySet.use_for_related_fields)
        self.assertEqual(ChildRelatedProjectQuerySet.project_field, 'child')
        self.assertTrue(ChildRelatedProjectQuerySet.use_for_related_fields)

    def test_subproject_queryset_as_manager_gets_correct_class(self):
        mgr = ChildRelatedProjectQuerySet.as_manager()
        self.assertEqual(
            mgr.__class__.__name__,
            'ManagerFromChildRelatedProjectQuerySetBase',
        )
        mgr = ParentRelatedProjectQuerySet.as_manager()
        self.assertEqual(
            mgr.__class__.__name__,
            'ManagerFromParentRelatedProjectQuerySetBase',
        )

    def test_is_active(self):
        project = fixture.get(Project, skip=False)
        self.assertTrue(Project.objects.is_active(project))

        project = fixture.get(Project, skip=True)
        self.assertFalse(Project.objects.is_active(project))

        user = fixture.get(User)
        user.profile.banned = True
        user.profile.save()
        project = fixture.get(Project, skip=False, users=[user])
        self.assertFalse(Project.objects.is_active(project))


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
        self.assertQuerysetEqual(
            Feature.objects.for_project(project),
            [repr(feature1), repr(feature3)],
            ordered=False,
        )

    def test_feature_multiple_projects(self):
        project1 = fixture.get(Project, main_language_project=None)
        project2 = fixture.get(Project, main_language_project=None)
        feature = fixture.get(Feature, projects=[project1, project2])
        self.assertQuerysetEqual(
            Feature.objects.for_project(project1),
            [repr(feature)],
            ordered=False,
        )
