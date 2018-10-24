# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.forms import VersionForm
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import Project


class TestVersionForm(TestCase):

    def setUp(self):
        self.project = get(Project)

    def test_default_version_is_active(self):
        version = get(
            Version,
            project=self.project,
            active=False,
        )
        self.project.default_version = version.slug
        self.project.save()

        form = VersionForm(
            {
                'active': True,
                'privacy_level': PRIVATE,
            },
            instance=version
        )
        self.assertTrue(form.is_valid())

    def test_default_version_is_inactive(self):
        version = get(
            Version,
            project=self.project,
            active=True,
        )
        self.project.default_version = version.slug
        self.project.save()

        form = VersionForm(
            {
                'active': False,
                'privacy_level': PRIVATE,
            },
            instance=version
        )
        self.assertFalse(form.is_valid())
        self.assertIn('active', form.errors)
