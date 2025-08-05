from unittest import mock

import django_dynamic_fixture as fixture
from django.test import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.oauth.models import RemoteRepository, RemoteRepositoryRelation
from readthedocs.projects.constants import PRIVATE, SINGLE_VERSION_WITHOUT_TRANSLATIONS
from readthedocs.projects.models import Project

from .mixins import APIEndpointMixin


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=False,
    ALLOW_PRIVATE_REPOS=False,
)
@mock.patch("readthedocs.projects.tasks.builds.update_docs_task", mock.MagicMock())
class ProjectsEndpointTests(APIEndpointMixin):
    def test_projects_list(self):
        url = reverse("projects-list")

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-list"),
        )

    def test_number_of_queries_projects_list(self):
        another_project = get(
            Project,
            users=[self.me],
        )
        superproject = get(
            Project,
            users=[self.me],
        )
        subproject = get(
            Project,
            users=[self.me],
        )
        superproject.add_subproject(subproject)

        main_traslation = get(
            Project,
            users=[self.me],
            language="en",
        )
        translation = get(
            Project,
            users=[self.me],
            main_language_project=main_traslation,
            language="es",
        )
        url = reverse("projects-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        with self.assertNumQueries(16):
            response = self.client.get(url)
            assert response.status_code == 200
            assert len(response.json()["results"]) == 6

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_projects_list_privacy_levels_enabled(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse("projects-list"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), self._get_response_dict("projects-list"))

        self.project.privacy_level = "private"
        self.project.external_builds_privacy_level = "private"
        self.project.save()
        response = self.client.get(
            reverse("projects-list"),
        )
        self.assertEqual(response.status_code, 200)
        expected = self._get_response_dict("projects-list")
        expected["results"][0]["privacy_level"] = "private"
        expected["results"][0]["external_builds_privacy_level"] = "private"
        response = response.json()
        # We don't care about the modified date.
        expected["results"][0].pop("modified")
        response["results"][0].pop("modified")
        self.assertDictEqual(response, expected)

    def test_projects_list_filter_full_hit(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse("projects-list"),
            data={
                "name": self.project.name,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-list"),
        )

    def test_projects_list_filter_partial_hit(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse("projects-list"),
            data={
                "name": self.project.name[0:3],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-list"),
        )

    def test_projects_list_filter_miss(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse("projects-list"),
            data={
                "name": "63dadecd5323d789cafe09f01cda85fd",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-list-empty"),
        )

    def test_projects_detail_anonymous_user(self):
        url = reverse(
            "projects-detail",
            kwargs={
                "project_slug": self.project.slug,
            },
        )
        data = {
            "expand": ("active_versions," "permissions"),
        }
        expected_response = self._get_response_dict("projects-detail")
        expected_response["permissions"]["admin"] = False

        self.client.logout()

        # The project is public
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # The project is private
        Project.objects.filter(slug=self.project.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 404)

    def test_projects_detail(self):
        url = reverse(
            "projects-detail",
            kwargs={
                "project_slug": self.project.slug,
            },
        )
        data = {
            "expand": ("active_versions," "permissions"),
        }
        expected_response = self._get_response_dict("projects-detail")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # The project is public
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # The project is private
        Project.objects.filter(slug=self.project.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url, data)
        expected_response["privacy_level"] = "private"
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_detail_other_user(self):
        url = reverse(
            "projects-detail",
            kwargs={
                "project_slug": self.project.slug,
            },
        )
        data = {
            "expand": ("active_versions," "permissions"),
        }
        expected_response = self._get_response_dict("projects-detail")
        expected_response["permissions"]["admin"] = False

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # The project is public
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # The project is private
        self.project.privacy_level = PRIVATE
        self.project.save()
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 404)

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_own_projects_detail_privacy_levels_enabled(self):
        url = reverse(
            "projects-detail",
            kwargs={
                "project_slug": self.project.slug,
            },
        )
        query_params = {
            "expand": ("active_versions," "permissions"),
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url, query_params)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-detail"),
        )

        self.project.privacy_level = "private"
        self.project.external_builds_privacy_level = "private"
        self.project.save()
        response = self.client.get(url, query_params)
        self.assertEqual(response.status_code, 200)
        expected = self._get_response_dict("projects-detail")
        expected["privacy_level"] = "private"
        expected["external_builds_privacy_level"] = "private"
        expected["active_versions"][0]["privacy_level"] = "public"
        response = response.json()
        # We don't care about the modified date.
        expected.pop("modified")
        response.pop("modified")
        self.assertDictEqual(response, expected)

    def test_projects_superproject_anonymous_user(self):
        self._create_subproject()
        url = reverse(
            "projects-superproject",
            kwargs={
                "project_slug": self.subproject.slug,
            },
        )
        expected_response = self._get_response_dict("projects-superproject")

        self.client.logout()

        # The project is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # The project is private
        Project.objects.filter(slug=self.project.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_projects_superproject(self):
        self._create_subproject()

        url = reverse(
            "projects-superproject",
            kwargs={
                "project_slug": self.subproject.slug,
            },
        )
        expected_response = self._get_response_dict("projects-superproject")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # The project is private
        Project.objects.filter(slug=self.project.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url)
        expected_response["privacy_level"] = "private"
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_superproject_other_user(self):
        self._create_subproject()
        url = reverse(
            "projects-superproject",
            kwargs={
                "project_slug": self.subproject.slug,
            },
        )
        expected_response = self._get_response_dict("projects-superproject")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # The project is private
        self.project.privacy_level = PRIVATE
        self.project.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_projects_sync_versions(self):
        # Ensure a default version exists to sync
        self.project.update_latest_version()

        url = reverse(
            "projects-sync-versions",
            kwargs={
                "project_slug": self.project.slug,
            },
        )

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        # Test with a user that is not the owner
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 202)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-sync-versions"),
        )

    def test_others_projects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-detail",
                kwargs={
                    "project_slug": self.others_project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_unauthed_others_projects_detail(self):
        response = self.client.get(
            reverse(
                "projects-detail",
                kwargs={
                    "project_slug": self.others_project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_nonexistent_projects_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-detail",
                kwargs={
                    "project_slug": "nonexistent",
                },
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_import_project(self):
        data = {
            "name": "Test Project",
            "repository": {
                "url": "https://github.com/rtfd/template",
                "type": "git",
            },
            "homepage": "http://template.readthedocs.io/",
            "programming_language": "py",
            "tags": ["test tag", "template tag"],
        }
        url = reverse("projects-list")

        self.client.logout()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)

        query = Project.objects.filter(slug="test-project")
        self.assertTrue(query.exists())

        project = query.first()
        self.assertIsNone(project.remote_repository)
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.slug, "test-project")
        self.assertEqual(project.repo, "https://github.com/rtfd/template")
        self.assertEqual(project.language, "en")
        self.assertEqual(project.programming_language, "py")
        self.assertEqual(project.project_url, "http://template.readthedocs.io/")
        self.assertEqual(list(project.tags.names()), ["template tag", "test tag"])
        self.assertIn(self.me, project.users.all())
        self.assertEqual(project.builds.count(), 1)

        response_json = response.json()
        response_json["created"] = "2019-04-29T10:00:00Z"
        response_json["modified"] = "2019-04-29T12:00:00Z"

        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-list_POST"),
        )

    def test_import_existing_project(self):
        fixture.get(
            Project,
            slug="test-project",
            name="Test Project",
        )
        data = {
            "name": "Test Project",
            "repository": {
                "url": "https://github.com/rtfd/template",
                "type": "git",
            },
            "homepage": "http://template.readthedocs.io/",
            "programming_language": "py",
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(reverse("projects-list"), data)
        self.assertContains(
            response,
            'Project with slug \\"test-project\\" already exists.',
            status_code=400,
        )

    def test_import_empty_slug(self):
        data = {
            "name": "*",
            "repository": {
                "url": "https://github.com/rtfd/template",
                "type": "git",
            },
            "homepage": "http://template.readthedocs.io/",
            "programming_language": "py",
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(reverse("projects-list"), data)
        self.assertContains(
            response,
            'Invalid project name \\"*\\": no slug generated.',
            status_code=400,
        )

    def test_import_project_with_extra_fields(self):
        data = {
            "name": "Test Project",
            "repository": {
                "url": "https://github.com/rtfd/template",
                "type": "git",
            },
            "default_version": "v1.0",  # ignored: field not allowed
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(reverse("projects-list"), data)
        self.assertEqual(response.status_code, 201)

        query = Project.objects.filter(slug="test-project")
        self.assertTrue(query.exists())

        project = query.first()
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.slug, "test-project")
        self.assertEqual(project.repo, "https://github.com/rtfd/template")
        self.assertNotEqual(project.default_version, "v1.0")
        self.assertIn(self.me, project.users.all())

    def test_import_project_with_remote_repository(self):
        remote_repository = fixture.get(
            RemoteRepository,
            full_name="rtfd/template",
            clone_url="https://github.com/rtfd/template",
            html_url="https://github.com/rtfd/template",
            ssh_url="git@github.com:rtfd/template.git",
            private=False,
        )
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repository,
            user=self.me,
            admin=True,
        )

        data = {
            "name": "Test Project",
            "repository": {
                "url": "https://github.com/rtfd/template",
                "type": "git",
            },
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(reverse("projects-list"), data)
        self.assertEqual(response.status_code, 201)

        query = Project.objects.filter(slug="test-project")
        self.assertTrue(query.exists())

        project = query.first()
        self.assertIsNotNone(project.remote_repository)
        self.assertEqual(project.remote_repository, remote_repository)

    def test_import_project_with_remote_repository_from_other_user(self):
        repo_url = "https://github.com/readthedocs/template"
        remote_repository = get(
            RemoteRepository,
            full_name="readthedocs/template",
            clone_url=repo_url,
            html_url="https://github.com/readthedocs/template",
            ssh_url="git@github.com:readthedocs/template.git",
            private=False,
        )

        data = {
            "name": "Test Project",
            "repository": {
                "url": repo_url,
                "type": "git",
            },
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.post(reverse("projects-list"), data)
        self.assertEqual(response.status_code, 201)
        project = Project.objects.get(slug=response.data["slug"])
        self.assertIsNone(project.remote_repository)

        # The user has access to the repository but is not an admin,
        # and the repository is private.
        remote_repository.private = True
        remote_repository.save()
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repository,
            user=self.me,
            admin=False,
        )

        data["name"] = "Test Project 2"
        response = self.client.post(reverse("projects-list"), data)
        self.assertEqual(response.status_code, 201)
        project = Project.objects.get(slug=response.data["slug"])
        self.assertIsNone(project.remote_repository)

    def test_update_project(self):
        data = {
            "name": "Updated name",
            "repository": {
                "url": "https://bitbucket.com/rtfd/updated-repository",
                "type": "git",
            },
            "language": "es",
            "programming_language": "js",
            "homepage": "https://updated-homepage.org",
            "tags": ["updated tag", "test tag"],
            "default_version": "stable",
            "default_branch": "updated-default-branch",
            "analytics_code": "UA-XXXXXX",
            "show_version_warning": False,
            "versioning_scheme": SINGLE_VERSION_WITHOUT_TRANSLATIONS,
            "external_builds_enabled": True,
        }
        url = reverse(
            "projects-detail",
            kwargs={
                "project_slug": self.project.slug,
            },
        )

        self.client.logout()
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 204)

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated name")
        self.assertEqual(self.project.slug, "project")
        self.assertEqual(
            self.project.repo, "https://bitbucket.com/rtfd/updated-repository"
        )
        self.assertEqual(self.project.repo_type, "git")
        self.assertEqual(self.project.language, "es")
        self.assertEqual(self.project.programming_language, "js")
        self.assertEqual(self.project.project_url, "https://updated-homepage.org")
        self.assertEqual(list(self.project.tags.names()), ["test tag", "updated tag"])
        self.assertEqual(self.project.default_version, "stable")
        self.assertEqual(self.project.default_branch, "updated-default-branch")
        self.assertEqual(self.project.analytics_code, "UA-XXXXXX")
        self.assertEqual(self.project.show_version_warning, False)
        self.assertEqual(self.project.is_single_version, True)
        self.assertEqual(self.project.external_builds_enabled, True)
        self.assertEqual(
            self.project.versioning_scheme, SINGLE_VERSION_WITHOUT_TRANSLATIONS
        )

    def test_partial_update_project(self):
        data = {
            "name": "Updated name",
            "repository": {
                "url": "https://github.com/rtfd/updated-repository",
            },
            "default_branch": "updated-default-branch",
            "tags": ["partial tags", "updated"],
        }

        url = reverse(
            "projects-detail",
            kwargs={
                "project_slug": self.project.slug,
            },
        )

        self.client.logout()
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 204)

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated name")
        self.assertEqual(self.project.slug, "project")
        self.assertEqual(
            self.project.repo, "https://github.com/rtfd/updated-repository"
        )
        self.assertEqual(list(self.project.tags.names()), ["partial tags", "updated"])
        self.assertNotEqual(self.project.default_version, "updated-default-branch")

    def test_partial_update_others_project(self):
        data = {
            "name": "Updated name",
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.patch(
            reverse(
                "projects-detail",
                kwargs={
                    "project_slug": self.others_project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 403)

    def test_partial_update_project_privacy_levels_disabled(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "private",
            "external_builds_privacy_level": "private",
        }
        response = self.client.patch(
            reverse(
                "projects-detail",
                kwargs={
                    "project_slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)

        self.project.refresh_from_db()
        self.assertEqual(self.project.privacy_level, "public")
        self.assertEqual(self.project.external_builds_privacy_level, "public")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_partial_update_project_privacy_levels_enabled(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "private",
            "external_builds_privacy_level": "private",
        }
        response = self.client.patch(
            reverse(
                "projects-detail",
                kwargs={
                    "project_slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)

        self.project.refresh_from_db()
        self.assertEqual(self.project.privacy_level, "private")
        self.assertEqual(self.project.external_builds_privacy_level, "private")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_partial_update_project_invalid_privacy_level(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "prubic",
            "external_builds_privacy_level": "privic",
        }
        response = self.client.patch(
            reverse(
                "projects-detail",
                kwargs={
                    "project_slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.project.refresh_from_db()
        self.assertEqual(self.project.privacy_level, "public")
        self.assertEqual(self.project.external_builds_privacy_level, "public")

    def test_projects_notifications_list(self):
        url = reverse(
            "projects-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-notifications-list"),
        )

    def test_projects_notifications_list_other_user(self):
        url = reverse(
            "projects-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_projects_notifications_list_post(self):
        url = reverse(
            "projects-notifications-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )

        self.client.logout()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(url)

        # We don't allow POST on this endpoint
        self.assertEqual(response.status_code, 405)

    def test_projects_notifications_detail(self):
        url = reverse(
            "projects-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "notification_pk": self.notification_project.pk,
            },
        )

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-notifications-detail"),
        )

    def test_projects_notifications_detail_other_user(self):
        url = reverse(
            "projects-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "notification_pk": self.notification_project.pk,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_projects_notifications_detail_patch(self):
        url = reverse(
            "projects-notifications-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "notification_pk": self.notification_project.pk,
            },
        )
        data = {
            "state": "read",
        }

        self.client.logout()
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 401)

        self.assertEqual(self.project.notifications.first().state, "unread")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.project.notifications.first().state, "read")
