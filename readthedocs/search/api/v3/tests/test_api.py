import itertools
from unittest import mock

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search.documents import PageDocument


@pytest.mark.search
class SearchTestBase(TestCase):
    def setUp(self):
        call_command("search_index", "--delete", "-f")
        call_command("search_index", "--create")

    def tearDown(self):
        super().tearDown()
        call_command("search_index", "--delete", "-f")

    def get_dummy_processed_json(self, extra=None):
        """
        Return a dict to be used as data indexed by ES.

        :param extra: By default it returns some default values,
                      you can override this passing a dict to extra.
        """
        extra = extra or {}
        default = {
            "path": "index.html",
            "title": "Title",
            "sections": [
                {
                    "id": "first",
                    "title": "First Paragraph",
                    "content": "First paragraph, content of interest: test.",
                }
            ],
            "domain_data": [],
        }
        default.update(extra)
        return default

    def create_index(self, version, files=None):
        """
        Create a search index for `version` with files as content.

        :param version: Version object
        :param files: A dictionary with the filename as key and a dict as value
                      to be passed to `get_dummy_processed_json`.
        """
        files = files or {"index.html": {}}
        for file, extra in files.items():
            html_file = HTMLFile.objects.filter(
                project=version.project, version=version, name=file
            ).first()
            if not html_file:
                html_file = get(
                    HTMLFile,
                    project=version.project,
                    version=version,
                    name=file,
                )
            html_file.get_processed_json = mock.MagicMock(
                name="get_processed_json",
                return_value=self.get_dummy_processed_json(extra),
            )
            PageDocument().update(html_file)


@override_settings(ALLOW_PRIVATE_REPOS=False)
@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class SearchAPITest(SearchTestBase):
    def setUp(self):
        super().setUp()
        self.user = get(User)
        self.another_user = get(User)
        self.project = get(
            Project, slug="project", users=[self.user], privacy_level=PUBLIC
        )
        self.another_project = get(
            Project,
            slug="another-project",
            users=[self.another_user],
            privacy_level=PUBLIC,
        )

        self.project.versions.update(privacy_level=PUBLIC, active=True, built=True)
        self.version = self.project.versions.first()

        self.another_project.versions.update(
            privacy_level=PUBLIC, active=True, built=True
        )
        self.another_version = self.another_project.versions.first()

        self.url = reverse("search_api_v3")
        self.client.force_login(self.user)

        for version in Version.objects.all():
            self.create_index(version)

    def get(self, *args, **kwargs):
        return self.client.get(*args, **kwargs)

    def test_search_no_projects(self):
        resp = self.get(self.url, data={"q": "test"})

        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(results, [])
        self.assertEqual(projects, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_project(self):
        resp = self.get(self.url, data={"q": "project:project test"})

        self.assertEqual(resp.status_code, 200)
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects, [{"slug": "project", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

    def test_search_project_explicit_version(self):
        resp = self.get(self.url, data={"q": "project:project/latest test"})

        self.assertEqual(resp.status_code, 200)
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects, [{"slug": "project", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

        new_version = get(
            Version,
            project=self.project,
            slug="v2",
            privacy_level=PUBLIC,
            built=True,
            active=True,
        )
        self.create_index(new_version)
        resp = self.get(self.url, data={"q": "project:project/v2 test"})

        self.assertEqual(resp.status_code, 200)
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(projects, [{"slug": "project", "versions": [{"slug": "v2"}]}])
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

    def test_search_project_explicit_version_unexisting(self):
        resp = self.get(self.url, data={"q": "project:project/v3 test"})
        self.assertEqual(resp.status_code, 200)
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(projects, [])
        self.assertEqual(results, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_project_unexisting(self):
        resp = self.get(self.url, data={"q": "project:foobar/latest test"})
        self.assertEqual(resp.status_code, 200)
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(projects, [])
        self.assertEqual(results, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_project_valid_and_invalid(self):
        resp = self.get(
            self.url, data={"q": "project:foobar/latest project:project/latest test"}
        )
        self.assertEqual(resp.status_code, 200)
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects, [{"slug": "project", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

    def test_search_multiple_projects(self):
        resp = self.get(
            self.url, data={"q": "project:project project:another-project test"}
        )

        self.assertEqual(resp.status_code, 200)
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "latest"}]},
                {"slug": "another-project", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

    def test_search_user_me_anonymous_user(self):
        self.client.logout()
        resp = self.get(self.url, data={"q": "user:@me test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(projects, [])
        self.assertEqual(results, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_user_me_logged_in_user(self):
        self.client.force_login(self.user)
        resp = self.get(self.url, data={"q": "user:@me test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects, [{"slug": "project", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

        self.client.force_login(self.another_user)
        resp = self.get(self.url, data={"q": "user:@me test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects, [{"slug": "another-project", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

    def test_search_user_invalid_value(self):
        self.client.force_login(self.user)
        resp = self.get(self.url, data={"q": "user:test test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(projects, [])
        self.assertEqual(results, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_user_and_project(self):
        self.client.force_login(self.user)
        resp = self.get(
            self.url, data={"q": "user:@me project:another-project/latest test"}
        )
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "another-project", "versions": [{"slug": "latest"}]},
                {"slug": "project", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

    def test_search_subprojects(self):
        subproject = get(
            Project, slug="subproject", users=[self.user], privacy_level=PUBLIC
        )
        self.project.add_subproject(subproject)
        get(Version, slug="v2", project=self.project, active=True, built=True)
        get(Version, slug="v3", project=self.project, active=True, built=True)
        get(Version, slug="v2", project=subproject, active=True, built=True)
        get(Version, slug="v4", project=subproject, active=True, built=True)
        subproject.versions.update(built=True, active=True, privacy_level=PUBLIC)
        self.project.versions.update(built=True, active=True, privacy_level=PUBLIC)

        for version in itertools.chain(
            subproject.versions.all(), self.project.versions.all()
        ):
            self.create_index(version)

        # Search default version of the project and its subprojects.
        resp = self.get(self.url, data={"q": "subprojects:project test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "latest"}]},
                {"slug": "subproject", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the latest version.
        resp = self.get(self.url, data={"q": "subprojects:project/latest test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "latest"}]},
                {"slug": "subproject", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the v2 version.
        resp = self.get(self.url, data={"q": "subprojects:project/v2 test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "v2"}]},
                {"slug": "subproject", "versions": [{"slug": "v2"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the v3 version.
        # Only the main project has this version,
        # we will default to the default version of its subproject.
        resp = self.get(self.url, data={"q": "subprojects:project/v3 test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "v3"}]},
                {"slug": "subproject", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the v4 version.
        # The main project doesn't have this version,
        # we include results from its subprojects only.
        resp = self.get(self.url, data={"q": "subprojects:project/v4 test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects, [{"slug": "subproject", "versions": [{"slug": "v4"}]}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")


@pytest.mark.proxito
@override_settings(PUBLIC_DOMAIN="readthedocs.io")
class ProxiedSearchAPITest(SearchAPITest):
    host = "project.readthedocs.io"

    def get(self, *args, **kwargs):
        return self.client.get(*args, HTTP_HOST=self.host, **kwargs)

    def test_search_project_number_of_queries(self):
        # Default version
        with self.assertNumQueries(11):
            resp = self.get(self.url, data={"q": "project:project test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        with self.assertNumQueries(17):
            resp = self.get(
                self.url, data={"q": "project:project project:another-project test"}
            )
            assert resp.status_code == 200
            assert resp.data["results"]

        # With explicit version
        with self.assertNumQueries(10):
            resp = self.get(self.url, data={"q": "project:project/latest test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        with self.assertNumQueries(16):
            resp = self.get(
                self.url, data={"q": "project:project/latest project:another-project/latest test"}
            )
            assert resp.status_code == 200
            assert resp.data["results"]

    @mock.patch("readthedocs.search.api.v3.views.tasks.record_search_query.delay", new=mock.MagicMock())
    def test_search_project_number_of_queries_without_search_recording(self):
        # Default version
        with self.assertNumQueries(8):
            resp = self.get(self.url, data={"q": "project:project test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        with self.assertNumQueries(12):
            resp = self.get(
                self.url, data={"q": "project:project project:another-project test"}
            )
            assert resp.status_code == 200
            assert resp.data["results"]

        # With explicit version
        with self.assertNumQueries(8):
            resp = self.get(self.url, data={"q": "project:project/latest test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        with self.assertNumQueries(12):
            resp = self.get(
                self.url, data={"q": "project:project/latest project:another-project/latest test"}
            )
            assert resp.status_code == 200
            assert resp.data["results"]

    def test_search_subprojects_number_of_queries(self):
        subproject = get(
            Project,
            slug="subproject",
            users=[self.user],
            privacy_level=PUBLIC,
        )
        subproject.versions.update(built=True, active=True, privacy_level=PUBLIC)
        self.create_index(subproject.versions.first())
        self.project.add_subproject(subproject)

        # Search on default version.
        with self.assertNumQueries(16):
            resp = self.get(self.url, data={"q": "subprojects:project test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        # Search on explicit version.
        with self.assertNumQueries(14):
            resp = self.get(self.url, data={"q": "subprojects:project/latest test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        # Add subprojects.
        for i in range(3):
            subproject = get(
                Project,
                slug=f"subproject-{i}",
                users=[self.user],
                privacy_level=PUBLIC,
            )
            subproject.versions.update(built=True, active=True, privacy_level=PUBLIC)
            self.create_index(subproject.versions.first())
            self.project.add_subproject(subproject)

        # Search on default version.
        with self.assertNumQueries(26):
            resp = self.get(self.url, data={"q": "subprojects:project test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        # Search on explicit version.
        with self.assertNumQueries(23):
            resp = self.get(self.url, data={"q": "subprojects:project/latest test"})
            assert resp.status_code == 200
            assert resp.data["results"]

    @mock.patch("readthedocs.search.api.v3.views.tasks.record_search_query.delay", new=mock.MagicMock())
    def test_search_subprojects_number_of_queries_without_search_recording(self):
        subproject = get(
            Project,
            slug="subproject",
            users=[self.user],
            privacy_level=PUBLIC,
        )
        subproject.versions.update(built=True, active=True, privacy_level=PUBLIC)
        self.create_index(subproject.versions.first())
        self.project.add_subproject(subproject)

        # Search on default version.
        with self.assertNumQueries(10):
            resp = self.get(self.url, data={"q": "subprojects:project test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        # Search on explicit version.
        with self.assertNumQueries(10):
            resp = self.get(self.url, data={"q": "subprojects:project/latest test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        # Add subprojects.
        for i in range(3):
            subproject = get(
                Project,
                slug=f"subproject-{i}",
                users=[self.user],
                privacy_level=PUBLIC,
            )
            subproject.versions.update(built=True, active=True, privacy_level=PUBLIC)
            self.create_index(subproject.versions.first())
            self.project.add_subproject(subproject)

        # Search on default version.
        with self.assertNumQueries(13):
            resp = self.get(self.url, data={"q": "subprojects:project test"})
            assert resp.status_code == 200
            assert resp.data["results"]

        # Search on explicit version.
        with self.assertNumQueries(13):
            resp = self.get(self.url, data={"q": "subprojects:project/latest test"})
            assert resp.status_code == 200
            assert resp.data["results"]


@override_settings(ALLOW_PRIVATE_REPOS=True)
@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class SearchAPIWithOrganizationsTest(SearchTestBase):
    def setUp(self):
        super().setUp()

        self.user = get(User)
        self.member = get(User)
        self.project = get(Project, slug="project")
        self.project.versions.update(built=True, active=True, privacy_level=PRIVATE)
        self.version = self.project.versions.first()
        self.version_public = get(
            Version,
            slug="public",
            project=self.project,
            privacy_level=PUBLIC,
            active=True,
            built=True,
        )

        self.project_b = get(Project, slug="project-b")
        self.project_b.versions.update(built=True, active=True, privacy_level=PRIVATE)
        self.version_b = self.project_b.versions.first()
        self.version_b_public = get(
            Version,
            slug="public",
            project=self.project_b,
            privacy_level=PUBLIC,
            built=True,
            active=True,
        )

        self.organization = get(
            Organization, owners=[self.user], projects=[self.project, self.project_b]
        )

        self.team = get(
            Team,
            members=[self.member],
            organization=self.organization,
            projects=[self.project_b],
            access="readonly",
        )

        self.another_user = get(User)
        self.another_project = get(Project, slug="another-project")
        self.another_project.versions.update(
            built=True, active=True, privacy_level=PRIVATE
        )
        self.another_version = self.another_project.versions.first()
        self.another_version_public = get(
            Version,
            slug="public",
            project=self.another_project,
            privacy_level=PUBLIC,
            built=True,
            active=True,
        )

        self.another_organization = get(
            Organization, owners=[self.another_user], projects=[self.another_project]
        )

        self.url = reverse("search_api_v3")
        self.client.force_login(self.user)

        for version in Version.objects.all():
            self.create_index(version)

    def test_search_no_projects(self):
        resp = self.client.get(self.url, data={"q": "test"})

        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(results, [])
        self.assertEqual(projects, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_project(self):
        resp = self.client.get(self.url, data={"q": "project:project test"})

        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            projects, [{"slug": "project", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(resp.data["query"], "test")

    def test_search_project_explicit_version(self):
        resp = self.client.get(self.url, data={"q": "project:project/public test"})

        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            projects, [{"slug": "project", "versions": [{"slug": "public"}]}]
        )
        self.assertEqual(resp.data["query"], "test")

    def test_search_project_no_permissions(self):
        resp = self.client.get(self.url, data={"q": "project:another-project test"})

        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(results, [])
        self.assertEqual(projects, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_project_private_version_anonymous_user(self):
        self.client.logout()

        resp = self.client.get(self.url, data={"q": "project:project test"})

        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(results, [])
        self.assertEqual(projects, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_project_public_version_anonymous_user(self):
        self.client.logout()

        resp = self.client.get(self.url, data={"q": "project:project/public test"})

        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            projects, [{"slug": "project", "versions": [{"slug": "public"}]}]
        )
        self.assertEqual(resp.data["query"], "test")

    def test_search_multiple_projects(self):
        resp = self.client.get(
            self.url,
            data={
                "q": "project:project project:another-project/latest project:project-b/latest test"
            },
        )
        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(len(results), 2)
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "latest"}]},
                {"slug": "project-b", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(resp.data["query"], "test")

    def test_search_multiple_projects_team_member(self):
        self.client.force_login(self.member)

        resp = self.client.get(
            self.url,
            data={
                "q": "project:project project:another-project/latest project:project-b/latest test"
            },
        )
        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"]
        projects = resp.data["projects"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            projects, [{"slug": "project-b", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(resp.data["query"], "test")

    def test_search_user_me_anonymous_user(self):
        self.client.logout()
        resp = self.client.get(self.url, data={"q": "user:@me test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(projects, [])
        self.assertEqual(results, [])
        self.assertEqual(resp.data["query"], "test")

    def test_search_user_me_logged_in_user(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url, data={"q": "user:@me test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "latest"}]},
                {"slug": "project-b", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

        self.client.force_login(self.member)
        resp = self.client.get(self.url, data={"q": "user:@me test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects, [{"slug": "project-b", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

        self.client.force_login(self.another_user)
        resp = self.client.get(self.url, data={"q": "user:@me test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects, [{"slug": "another-project", "versions": [{"slug": "latest"}]}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

    def test_search_user_and_project(self):
        self.client.force_login(self.member)
        resp = self.client.get(
            self.url, data={"q": "user:@me project:another-project/public test"}
        )
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "another-project", "versions": [{"slug": "public"}]},
                {"slug": "project-b", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

    def test_search_subprojects(self):
        self.project.add_subproject(self.project_b)

        # Search default version of the project and its subprojects.
        resp = self.client.get(self.url, data={"q": "subprojects:project test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "latest"}]},
                {"slug": "project-b", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the latest version.
        resp = self.client.get(self.url, data={"q": "subprojects:project/latest test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "latest"}]},
                {"slug": "project-b", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the public version.
        resp = self.client.get(self.url, data={"q": "subprojects:project/public test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "public"}]},
                {"slug": "project-b", "versions": [{"slug": "public"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

    def test_search_subprojects_with_team_member(self):
        self.client.force_login(self.member)
        self.project.add_subproject(self.project_b)

        # Search default version of the project and its subprojects.
        resp = self.client.get(self.url, data={"q": "subprojects:project test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project-b", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the latest version.
        resp = self.client.get(self.url, data={"q": "subprojects:project/latest test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project-b", "versions": [{"slug": "latest"}]},
            ],
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the public version.
        resp = self.client.get(self.url, data={"q": "subprojects:project/public test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "public"}]},
                {"slug": "project-b", "versions": [{"slug": "public"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")

    def test_search_subprojects_with_anonymous_user(self):
        self.client.logout()
        self.project.add_subproject(self.project_b)

        # Search default version of the project and its subprojects.
        resp = self.client.get(self.url, data={"q": "subprojects:project test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [],
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the latest version.
        resp = self.client.get(self.url, data={"q": "subprojects:project/latest test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [],
        )
        self.assertEqual(len(results), 0)
        self.assertEqual(resp.data["query"], "test")

        # Explicitly search on the public version.
        resp = self.client.get(self.url, data={"q": "subprojects:project/public test"})
        projects = resp.data["projects"]
        results = resp.data["results"]
        self.assertEqual(
            projects,
            [
                {"slug": "project", "versions": [{"slug": "public"}]},
                {"slug": "project-b", "versions": [{"slug": "public"}]},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.data["query"], "test")
