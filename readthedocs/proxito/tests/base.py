# Copied from .org


import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.models import Project


@override_settings(
    PUBLIC_DOMAIN='dev.readthedocs.io',
    ROOT_URLCONF='readthedocs.proxito.urls',
    MIDDLEWARE=['readthedocs.proxito.middleware.ProxitoMiddleware'],
    USE_SUBDOMAIN=True,
)
class BaseDocServing(TestCase):

    def setUp(self):
        self.eric = fixture.get(User, username='eric')
        self.eric.set_password('eric')
        self.eric.save()
        self.private = fixture.get(
            Project, slug='private', privacy_level='private',
            version_privacy_level='private', users=[self.eric],
            main_language_project=None,
        )
        self.subproject = fixture.get(
            Project,
            slug='subproject',
            users=[self.eric],
            main_language_project=None,
        )
        self.private.add_subproject(self.subproject)
