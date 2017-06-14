from __future__ import absolute_import
from django.test import TestCase
from django.test.utils import override_settings

import django_dynamic_fixture as fixture

from readthedocs.projects.models import Project


@override_settings(
    USE_SUBDOMAIN=True, PUBLIC_DOMAIN='public.readthedocs.org', SERVE_PUBLIC_DOCS=True
)
class RedirectSingleVersionTests(TestCase):

    def setUp(self):
        self.pip = fixture.get(Project, slug='pip', single_version=True, main_language_project=None)

    def test_docs_url_generation(self):
        with override_settings(USE_SUBDOMAIN=False):
            self.assertEqual(self.pip.get_docs_url(),
                             'http://readthedocs.org/docs/pip/')
        with override_settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.pip.get_docs_url(),
                             'http://pip.public.readthedocs.org/')

        self.pip.single_version = False
        with override_settings(USE_SUBDOMAIN=False):
            self.assertEqual(self.pip.get_docs_url(),
                             'http://readthedocs.org/docs/pip/en/latest/')
        with override_settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.pip.get_docs_url(),
                             'http://pip.public.readthedocs.org/en/latest/')
