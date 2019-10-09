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
        self.project = fixture.get(
            Project, slug='project', privacy_level='project',
            version_privacy_level='project', users=[self.eric],
            main_language_project=None,
        )
        self.subproject = fixture.get(
            Project,
            slug='subproject',
            users=[self.eric],
            main_language_project=None,
        )
        self.project.add_subproject(self.subproject)
        self.translation = fixture.get(
            Project,
            language='es',
            slug='translation',
            users=[self.eric],
            main_language_project=self.project,
        )
        self.subproject_translation = fixture.get(
            Project,
            language='es',
            slug='subproject-translation',
            users=[self.eric],
            main_language_project=self.subproject,
        )
        self.subproject_alias = fixture.get(
            Project,
            language='en',
            slug='subproject-alias',
            users=[self.eric],
        )
        self.project.add_subproject(self.subproject_alias, alias='this-is-an-alias')
