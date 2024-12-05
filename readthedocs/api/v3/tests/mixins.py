import datetime
import json
from pathlib import Path

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import make_aware
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from readthedocs.builds.constants import LATEST, TAG
from readthedocs.builds.models import Build, Version
from readthedocs.core.notifications import MESSAGE_EMAIL_VALIDATION_PENDING
from readthedocs.doc_builder.exceptions import BuildCancelled
from readthedocs.notifications.models import Notification
from readthedocs.organizations.models import Organization
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project
from readthedocs.projects.notifications import MESSAGE_PROJECT_SKIP_BUILDS
from readthedocs.redirects.models import Redirect
from readthedocs.subscriptions.notifications import MESSAGE_ORGANIZATION_DISABLED


@override_settings(
    PUBLIC_DOMAIN="readthedocs.io",
    PRODUCTION_DOMAIN="readthedocs.org",
    RTD_EXTERNAL_VERSION_DOMAIN="external-builds.readthedocs.io",
    RTD_BUILD_MEDIA_STORAGE="readthedocs.rtd_tests.storage.BuildMediaFileSystemStorageTest",
    RTD_ALLOW_ORGANIZATIONS=False,
)
class APIEndpointMixin(TestCase):
    fixtures = []
    maxDiff = None  # So we get an actual diff when it fails

    def setUp(self):
        self.created = make_aware(datetime.datetime(2019, 4, 29, 10, 0, 0))
        self.modified = make_aware(datetime.datetime(2019, 4, 29, 12, 0, 0))

        self.me = fixture.get(
            User,
            date_joined=self.created,
            username="testuser",
            projects=[],
        )
        self.token = fixture.get(Token, key="me", user=self.me)
        # Defining all the defaults helps to avoid creating ghost / unwanted
        # objects (like a Project for translations/subprojects)
        self.project = fixture.get(
            Project,
            id=1,
            pub_date=self.created,
            modified_date=self.modified,
            description="Project description",
            repo="https://github.com/rtfd/project",
            project_url="http://project.com",
            name="project",
            slug="project",
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
            external_builds_enabled=False,
            external_builds_privacy_level=PUBLIC,
            privacy_level=PUBLIC,
        )
        for tag in ("tag", "project", "test"):
            self.project.tags.add(tag)

        self.redirect = fixture.get(
            Redirect,
            create_dt=self.created,
            update_dt=self.modified,
            from_url="/docs/",
            to_url="/documentation/",
            redirect_type="page",
            project=self.project,
        )

        self.version = fixture.get(
            Version,
            slug="v1.0",
            verbose_name="v1.0",
            identifier="a1b2c3",
            project=self.project,
            hidden=False,
            active=True,
            built=True,
            type=TAG,
            has_pdf=True,
            has_epub=True,
            has_htmlzip=True,
            privacy_level=PUBLIC,
        )

        self.build = fixture.get(
            Build,
            id=1,
            date=self.created,
            type="html",
            state="finished",
            error="",
            success=True,
            _config={"property": "test value"},
            version=self.version,
            project=self.project,
            builder="builder01",
            commit="a1b2c3",
            length=60,
        )

        self.other = fixture.get(User, projects=[])
        self.others_token = fixture.get(Token, key="other", user=self.other)
        self.others_project = fixture.get(
            Project,
            id=2,
            slug="others-project",
            name="others-project",
            related_projects=[],
            main_language_project=None,
            users=[self.other],
            versions=[],
            external_builds_privacy_level=PUBLIC,
            privacy_level=PUBLIC,
        )
        self.others_version = self.others_project.versions.get(slug=LATEST)
        self.others_build = fixture.get(
            Build,
            date=self.created,
            type="html",
            state="finished",
            error="",
            success=True,
            _config={"property": "test value"},
            version=self.others_version,
            project=self.others_project,
            builder="builder01",
            commit="a1b2c3",
            length=60,
        )

        # Make all non-html true so responses are complete
        self.project.versions.update(
            has_pdf=True,
            has_epub=True,
            has_htmlzip=True,
            privacy_level=PUBLIC,
        )

        self.organization = fixture.get(
            Organization,
            id=1,
            pub_date=self.created,
            modified_date=self.modified,
            name="organization",
            slug="organization",
            owners=[self.me],
        )
        self.organization.projects.add(self.project)

        self.notification_organization = fixture.get(
            Notification,
            attached_to_content_type=ContentType.objects.get_for_model(
                self.organization
            ),
            attached_to_id=self.organization.pk,
            message_id=MESSAGE_ORGANIZATION_DISABLED,
        )
        self.notification_project = fixture.get(
            Notification,
            attached_to_content_type=ContentType.objects.get_for_model(self.project),
            attached_to_id=self.project.pk,
            message_id=MESSAGE_PROJECT_SKIP_BUILDS,
        )
        self.notification_build = fixture.get(
            Notification,
            attached_to_content_type=ContentType.objects.get_for_model(self.build),
            attached_to_id=self.build.pk,
            message_id=BuildCancelled.CANCELLED_BY_USER,
        )
        self.notification_user = fixture.get(
            Notification,
            attached_to_content_type=ContentType.objects.get_for_model(self.me),
            attached_to_id=self.me.pk,
            message_id=MESSAGE_EMAIL_VALIDATION_PENDING,
        )

        self.notification_others_build = fixture.get(
            Notification,
            attached_to_content_type=ContentType.objects.get_for_model(Build),
            attached_to_id=self.others_build.pk,
            message_id=BuildCancelled.CANCELLED_BY_USER,
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
            description="Project description",
            repo="https://github.com/rtfd/project",
            project_url="http://project.com",
            name="new-project",
            slug="new-project",
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
            external_builds_privacy_level=PUBLIC,
            privacy_level=PUBLIC,
        )

    def _create_subproject(self):
        """Helper to create a sub-project with all the fields set."""
        self.subproject = fixture.get(
            Project,
            pub_date=self.created,
            modified_date=self.modified,
            description="SubProject description",
            repo="https://github.com/rtfd/subproject",
            project_url="http://subproject.com",
            name="subproject",
            slug="subproject",
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
            external_builds_privacy_level=PUBLIC,
            privacy_level=PUBLIC,
        )
        self.project_relationship = self.project.add_subproject(self.subproject)

    def _get_response_dict(self, view_name, filepath=None):
        filepath = filepath or __file__
        filename = Path(filepath).absolute().parent / "responses" / f"{view_name}.json"
        return json.load(open(filename))

    def assertDictEqual(self, d1, d2):
        """
        Show the differences between the dicts in a human readable way.

        It's just a helper for debugging API responses.
        """
        message = ""
        try:
            import datadiff

            message = datadiff.diff(d1, d2)
        except ImportError:
            pass
        return super().assertDictEqual(d1, d2, message)
