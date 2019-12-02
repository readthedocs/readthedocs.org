# Copied from .org


import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project


@override_settings(
    PUBLIC_DOMAIN='dev.readthedocs.io',
    ROOT_URLCONF='readthedocs.proxito.urls',
    MIDDLEWARE=[
        # Auth middleware is required since some views uses ``request.user``
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',

        'readthedocs.proxito.middleware.ProxitoMiddleware',
    ],
    USE_SUBDOMAIN=True,
    RTD_BUILD_MEDIA_STORAGE='readthedocs.rtd_tests.storage.BuildMediaFileSystemStorageTest',
)
class BaseDocServing(TestCase):

    def setUp(self):
        self.eric = fixture.get(User, username='eric')
        self.eric.set_password('eric')
        self.eric.save()
        self.project = fixture.get(
            Project,
            slug='project',
            privacy_level=PUBLIC,
            version_privacy_level=PUBLIC,
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
