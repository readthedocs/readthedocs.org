from __future__ import absolute_import

from datetime import timedelta

import django_dynamic_fixture as fixture
from django.test import TestCase

from readthedocs.projects.models import Project, ProjectRelationship, Feature
from readthedocs.projects.querysets import (ParentRelatedProjectQuerySet,
                                            ChildRelatedProjectQuerySet)


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
            'ManagerFromChildRelatedProjectQuerySetBase'
        )
        mgr = ParentRelatedProjectQuerySet.as_manager()
        self.assertEqual(
            mgr.__class__.__name__,
            'ManagerFromParentRelatedProjectQuerySetBase'
        )


class FeatureQuerySetTests(TestCase):

    def test_feature_for_project_is_explicit_applied(self):
        project = fixture.get(Project, main_language_project=None)
        feature = fixture.get(Feature, projects=[project])
        self.assertTrue(project.has_feature(feature.feature))

    def test_feature_for_project_is_implicitly_applied(self):
        project = fixture.get(Project, main_language_project=None)
        feature1 = fixture.get(Feature, projects=[project])
        feature2 = fixture.get(
            Feature,
            projects=[],
            add_date=project.pub_date + timedelta(days=1),
            default_true=False,
        )
        feature3 = fixture.get(
            Feature,
            projects=[],
            add_date=project.pub_date + timedelta(days=1),
            default_true=True,
        )
        self.assertTrue(project.has_feature(feature1.feature))
        self.assertFalse(project.has_feature(feature2.feature))
        self.assertTrue(project.has_feature(feature3.feature))
