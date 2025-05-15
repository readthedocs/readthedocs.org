# Copied from .org

import django_dynamic_fixture as fixture
import pytest
from django.conf import settings
from django.contrib.auth.models import User
from readthedocs.storage import get_storage_class
from django.test import TestCase

from readthedocs.builds.constants import LATEST
from readthedocs.projects.constants import PUBLIC, SSL_STATUS_VALID
from readthedocs.projects.models import Domain, Project
from readthedocs.proxito.views import serve


@pytest.mark.proxito
class BaseDocServing(TestCase):
    def setUp(self):
        # Re-initialize storage
        # Various tests override either this setting or various aspects of the storage engine
        # By resetting it every test case, we avoid this caching (which is a huge benefit in prod)
        serve.build_media_storage = get_storage_class(
            settings.RTD_BUILD_MEDIA_STORAGE
        )()

        self.eric = fixture.get(User, username="eric")
        self.eric.set_password("eric")
        self.eric.save()
        self.project = fixture.get(
            Project,
            slug="project",
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
            users=[self.eric],
            main_language_project=None,
        )
        self.project.versions.update(privacy_level=PUBLIC, built=True, active=True)
        self.version = self.project.versions.get(slug=LATEST)

        self.subproject = fixture.get(
            Project,
            slug="subproject",
            users=[self.eric],
            main_language_project=None,
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
        )
        self.subproject.versions.update(privacy_level=PUBLIC)
        self.project.add_subproject(self.subproject)
        self.translation = fixture.get(
            Project,
            language="es",
            slug="translation",
            users=[self.eric],
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
            main_language_project=self.project,
        )
        self.translation.versions.update(privacy_level=PUBLIC)

        self.subproject_translation = fixture.get(
            Project,
            language="es",
            slug="subproject-translation",
            users=[self.eric],
            main_language_project=self.subproject,
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
        )
        self.subproject_translation.versions.update(privacy_level=PUBLIC)

        self.subproject_alias = fixture.get(
            Project,
            language="en",
            slug="subproject-alias",
            users=[self.eric],
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
        )
        self.subproject_alias.versions.update(privacy_level=PUBLIC)
        self.project.add_subproject(self.subproject_alias, alias="this-is-an-alias")

        # These can be set to canonical as needed in specific tests
        self.domain = fixture.get(
            Domain,
            project=self.project,
            domain="docs1.example.com",
            https=True,
            ssl_status=SSL_STATUS_VALID,
        )
        self.domain2 = fixture.get(
            Domain,
            project=self.project,
            domain="docs2.example.com",
            https=True,
            ssl_status=SSL_STATUS_VALID,
        )
