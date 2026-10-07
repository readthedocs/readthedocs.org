from unittest import mock

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

    def test_register_page_view(self):
        for _ in range(3):
            PageView.objects.register_page_view(
                project=self.project,
                version=self.version,
                filename="index.html",
                path="/en/latest/index.html",
                status=200,
            )

        page_view = PageView.objects.get()
        assert page_view.view_count == 3
        assert page_view.path == "/index.html"
        assert page_view.full_path == "/en/latest/index.html"

    def test_register_page_view_without_version(self):
        for _ in range(2):
            PageView.objects.register_page_view(
                project=self.project,
                version=None,
                filename="/missing.html",
                path="/missing.html",
                status=404,
            )

        page_view = PageView.objects.get()
        assert page_view.version is None
        assert page_view.view_count == 2

    def test_register_page_view_with_hit_is_a_single_query(self):
        kwargs = {
            "project": self.project,
            "version": self.version,
            "filename": "/index.html",
            "path": "/en/latest/index.html",
            "status": 200,
        }
        PageView.objects.register_page_view(**kwargs)
        # One query to check the feature flag, and a single UPDATE.
        with self.assertNumQueries(2):
            PageView.objects.register_page_view(**kwargs)
        assert PageView.objects.get().view_count == 2

    def test_register_page_view_created_concurrently(self):
        """The row is created by another request between our UPDATE and INSERT."""
        PageView.objects.create(
            project=self.project,
            version=self.version,
            path="/index.html",
            status=200,
            view_count=1,
        )
        increase_view_count = PageView.objects._increase_view_count
        calls = []

        def fake_increase_view_count(lookup):
            calls.append(lookup)
            # Pretend the row didn't exist yet on the first UPDATE.
            if len(calls) == 1:
                return 0
            return increase_view_count(lookup)

        with mock.patch.object(
            PageView.objects,
            "_increase_view_count",
            side_effect=fake_increase_view_count,
        ):
            PageView.objects.register_page_view(
                project=self.project,
                version=self.version,
                filename="/index.html",
                path="/en/latest/index.html",
                status=200,
            )

        assert len(calls) == 2
        assert PageView.objects.get().view_count == 2
