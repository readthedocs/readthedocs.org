# -*- coding: utf-8 -*-
"""Tests For SVN"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from mock import patch
from django_dynamic_fixture import get

from readthedocs.rtd_tests.base import RTDTestCase
from readthedocs.projects.models import Project
from readthedocs.builds.models import Version
from readthedocs.vcs_support.backends.svn import Backend as SvnBackend

class TestSvnBackend(RTDTestCase):

    def setUp(self):
        super(TestSvnBackend, self).setUp()

    def test_get_url(self):
        project = get(Project)
        version = get(Version, project=project)
        backend_obj = SvnBackend(project, version.slug)

        base = 'http://example.com/'
        tag = 'xyz/'
        self.assertEqual(backend_obj.get_url(base, tag), 'http://example.com/xyz/')

        base = 'http://example.com/'
        tag = '/xyz/'
        self.assertEqual(backend_obj.get_url(base, tag), 'http://example.com/xyz/')

        base = 'http://example.com'
        tag = '/xyz/'
        self.assertEqual(backend_obj.get_url(base, tag), 'http://example.com/xyz/')
