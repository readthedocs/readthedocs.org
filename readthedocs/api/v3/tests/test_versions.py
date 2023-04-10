import django_dynamic_fixture as fixture
from django.test import override_settings
from django.urls import reverse

from readthedocs.builds.constants import EXTERNAL, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project

from .mixins import APIEndpointMixin


@override_settings(ALLOW_PRIVATE_REPOS=False)
class VersionsEndpointTests(APIEndpointMixin):

    def test_projects_versions_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-list',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["slug"], "v1.0")
        self.assertEqual(response["results"][1]["slug"], "latest")

    def test_others_projects_versions_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-list',
                kwargs={
                    'parent_lookup_project__slug': self.others_project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_projects_versions_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'version_slug': 'v1.0',
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict('projects-versions-detail'),
        )

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_projects_versions_detail_privacy_levels_allowed(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-versions-detail"),
        )

        self.version.privacy_level = "private"
        self.version.save()
        response = self.client.get(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        expected = self._get_response_dict("projects-versions-detail")
        expected["privacy_level"] = "private"
        self.assertDictEqual(
            response.json(),
            expected,
        )

    def test_nonexistent_project_version_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-detail',
                kwargs={
                    'parent_lookup_project__slug': 'nonexistent',
                    'version_slug': 'latest',
                },
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_projects_versions_detail_unique(self):
        second_project = fixture.get(
            Project,
            name='second project',
            slug='second-project',
            related_projects=[],
            main_language_project=None,
            users=[self.me],
            versions=[],
        )
        second_version = fixture.get(
            Version,
            slug=self.version.slug,
            verbose_name=self.version.verbose_name,
            identifier='a1b2c3',
            project=second_project,
            active=True,
            built=True,
            type=TAG,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(
            reverse(
                'projects-versions-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'version_slug': self.version.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_projects_versions_partial_update(self):
        self.assertTrue(self.version.active)
        self.assertFalse(self.version.hidden)
        data = {
            'active': False,
            'hidden': True,
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.patch(
            reverse(
                'projects-versions-detail',
                kwargs={
                    'parent_lookup_project__slug': self.project.slug,
                    'version_slug': self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)

        self.version.refresh_from_db()
        self.assertEqual(self.version.verbose_name, 'v1.0')
        self.assertEqual(self.version.slug, 'v1.0')
        self.assertEqual(self.version.identifier, 'a1b2c3')
        self.assertFalse(self.version.active)
        self.assertTrue(self.version.hidden)
        self.assertTrue(self.version.built)
        self.assertEqual(self.version.type, TAG)

    def test_projects_versions_partial_update_privacy_levels_disabled(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "private",
        }
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)
        self.version.refresh_from_db()
        self.assertEqual(self.version.privacy_level, "public")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_projects_versions_partial_update_privacy_levels_enabled(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "private",
        }
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 204)
        self.version.refresh_from_db()
        self.assertEqual(self.version.privacy_level, "private")

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_projects_versions_partial_update_invalid_privacy_levels(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "privacy_level": "publicprivate",
        }
        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.version.privacy_level, "public")

    def test_projects_version_external(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.version.type = EXTERNAL
        self.version.save()

        response = self.client.get(
            reverse(
                "projects-versions-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0]["slug"], "latest")

        response = self.client.get(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.patch(
            reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "version_slug": self.version.slug,
                },
            ),
            data={
                "active": False,
            },
        )
        self.assertEqual(response.status_code, 404)
