from __future__ import absolute_import

import django_dynamic_fixture as fixture
from django.test import TestCase

from readthedocs.projects.models import Project, ProjectRelationship
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
