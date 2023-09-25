"""Tests For SVN."""

from unittest import mock

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.doc_builder.environments import LocalBuildEnvironment
from readthedocs.projects.models import Project
from readthedocs.vcs_support.backends.svn import Backend as SvnBackend


class TestSvnBackend(TestCase):
    def test_get_url(self):
        project = get(Project)
        version = get(Version, project=project)
        environment = LocalBuildEnvironment(api_client=mock.MagicMock())
        backend_obj = SvnBackend(project, version.slug, environment=environment)

        base = "http://example.com/"
        tag = "xyz/"
        self.assertEqual(backend_obj.get_url(base, tag), "http://example.com/xyz/")

        base = "http://example.com/"
        tag = "/xyz/"
        self.assertEqual(backend_obj.get_url(base, tag), "http://example.com/xyz/")

        base = "http://example.com"
        tag = "/xyz/"
        self.assertEqual(backend_obj.get_url(base, tag), "http://example.com/xyz/")
