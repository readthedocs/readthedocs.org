# Copied from .org


import pytest
import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project, Domain


@pytest.mark.proxito
class BaseDocServing(TestCase):

    def setUp(self):
        self.eric = fixture.get(User, username='eric')
        self.eric.set_password('eric')
        self.eric.save()
        self.project = fixture.get(
            Project,
            slug='project',
            privacy_level=PUBLIC,
            users=[self.eric],
            main_language_project=None,
        )
        self.project.versions.update(privacy_level=PUBLIC)

        self.subproject = fixture.get(
            Project,
            slug='subproject',
            users=[self.eric],
            main_language_project=None,
            privacy_level=PUBLIC,
        )
        self.subproject.versions.update(privacy_level=PUBLIC)
        self.project.add_subproject(self.subproject)
        self.translation = fixture.get(
            Project,
            language='es',
            slug='translation',
            users=[self.eric],
            privacy_level=PUBLIC,
            main_language_project=self.project,
        )
        self.translation.versions.update(privacy_level=PUBLIC)

        self.subproject_translation = fixture.get(
            Project,
            language='es',
            slug='subproject-translation',
            users=[self.eric],
            main_language_project=self.subproject,
            privacy_level=PUBLIC,
        )
        self.subproject_translation.versions.update(privacy_level=PUBLIC)

        self.subproject_alias = fixture.get(
            Project,
            language='en',
            slug='subproject-alias',
            users=[self.eric],
            privacy_level=PUBLIC,
        )
        self.subproject_alias.versions.update(privacy_level=PUBLIC)
        self.project.add_subproject(self.subproject_alias, alias='this-is-an-alias')

        # These can be set to canonical as needed in specific tests
        self.domain = fixture.get(Domain, project=self.project, domain='docs1.example.com', https=True)
        self.domain2 = fixture.get(Domain, project=self.project, domain='docs2.example.com', https=True)
