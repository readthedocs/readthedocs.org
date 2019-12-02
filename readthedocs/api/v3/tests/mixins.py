import datetime
import json
from pathlib import Path

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import make_aware
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project
from readthedocs.redirects.models import Redirect


@override_settings(
    PUBLIC_DOMAIN='readthedocs.io',
    PRODUCTION_DOMAIN='readthedocs.org',
    USE_SUBDOMAIN=True,
    RTD_BUILD_MEDIA_STORAGE='readthedocs.rtd_tests.storage.BuildMediaFileSystemStorageTest',
)
class APIEndpointMixin(TestCase):

    fixtures = []

    def setUp(self):
        self.created = make_aware(datetime.datetime(2019, 4, 29, 10, 0, 0))
        self.modified = make_aware(datetime.datetime(2019, 4, 29, 12, 0, 0))

        self.me = fixture.get(
            User,
            date_joined=self.created,
            username='testuser',
            projects=[],
        )
        self.token = fixture.get(Token, key='me', user=self.me)
        # Defining all the defaults helps to avoid creating ghost / unwanted
        # objects (like a Project for translations/subprojects)
        self.project = fixture.get(
            Project,
            pub_date=self.created,
            modified_date=self.modified,
            description='Project description',
            repo='https://github.com/rtfd/project',
            project_url='http://project.com',
            name='project',
            slug='project',
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
        )
        for tag in ('tag', 'project', 'test'):
            self.project.tags.add(tag)

        self.redirect = fixture.get(
            Redirect,
            create_dt=self.created,
            update_dt=self.modified,
            from_url='/docs/',
            to_url='/documentation/',
            redirect_type='page',
            project=self.project,
        )

        self.version = fixture.get(
            Version,
            slug='v1.0',
            verbose_name='v1.0',
            identifier='a1b2c3',
            project=self.project,
            active=True,
            built=True,
            type=TAG,
        )

        self.build = fixture.get(
            Build,
            date=self.created,
            type='html',
            state='finished',
            error='',
            success=True,
            _config = {'property': 'test value'},
            version=self.version,
            project=self.project,
            builder='builder01',
            commit='a1b2c3',
            length=60,
        )

        self.other = fixture.get(User, projects=[])
        self.others_token = fixture.get(Token, key='other', user=self.other)
        self.others_project = fixture.get(
            Project,
            slug='others-project',
            related_projects=[],
            main_language_project=None,
            users=[self.other],
            versions=[],
        )

        self.client = APIClient()

    def tearDown(self):
        # Cleanup cache to avoid throttling on tests
        cache.clear()

    def _create_new_project(self):
        """Helper to create a project with all the fields set."""
        return fixture.get(
            Project,
            pub_date=self.created,
            modified_date=self.modified,
            description='Project description',
            repo='https://github.com/rtfd/project',
            project_url='http://project.com',
            name='new-project',
            slug='new-project',
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
        )

    def _create_subproject(self):
        """Helper to create a sub-project with all the fields set."""
        self.subproject = fixture.get(
            Project,
            pub_date=self.created,
            modified_date=self.modified,
            description='SubProject description',
            repo='https://github.com/rtfd/subproject',
            project_url='http://subproject.com',
            name='subproject',
            slug='subproject',
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
        )
        self.project_relationship = self.project.add_subproject(self.subproject)

    def _get_response_dict(self, view_name):
        filename = Path(__file__).absolute().parent / 'responses' / f'{view_name}.json'
        return json.load(open(filename))

    def assertDictEqual(self, d1, d2):
        """
        Show the differences between the dicts in a human readable way.

        It's just a helper for debugging API responses.
        """
        import datadiff
        return super().assertDictEqual(d1, d2, datadiff.diff(d1, d2))
