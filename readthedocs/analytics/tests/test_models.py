import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.analytics.models import PageView
from readthedocs.projects.models import Project


class TestModels(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.version = self.project.versions.first()

    def test_unique_constraint(self):
        path = "/test"
        PageView.objects.create(
            path=path,
            project=self.project,
            version=self.version,
            status=200,
        )

        with pytest.raises(IntegrityError):
            PageView.objects.create(
                path=path,
                project=self.project,
                version=self.version,
                status=200,
            )

    def test_unique_constraint_null_version(self):
        path = "/test"
        PageView.objects.create(
            path=path,
            project=self.project,
            version=None,
            status=200,
        )

        with pytest.raises(IntegrityError):
            PageView.objects.create(
                path=path,
                project=self.project,
                version=None,
                status=200,
            )

    def test_records_with_and_without_version_can_exist(self):
        self.assertEqual(PageView.objects.all().count(), 0)
        path = "/test"
        PageView.objects.create(
            path=path,
            project=self.project,
            version=self.version,
            status=200,
        )
        PageView.objects.create(
            path=path,
            project=self.project,
            version=None,
            status=200,
        )
        self.assertEqual(PageView.objects.all().count(), 2)
