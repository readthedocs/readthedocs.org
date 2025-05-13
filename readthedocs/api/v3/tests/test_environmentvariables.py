import django_dynamic_fixture as fixture
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.projects.models import EnvironmentVariable
from readthedocs.projects.validators import MAX_SIZE_ENV_VARS_PER_PROJECT

from .mixins import APIEndpointMixin


class EnvironmentVariablessEndpointTests(APIEndpointMixin):
    def setUp(self):
        super().setUp()

        self.environmentvariable = fixture.get(
            EnvironmentVariable,
            created=self.created,
            modified=self.modified,
            project=self.project,
            name="ENVVAR",
            value="a1b2c3",
            public=False,
        )

    def test_unauthed_projects_environmentvariables_list(self):
        response = self.client.get(
            reverse(
                "projects-environmentvariables-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 401)

    def test_projects_environmentvariables_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-environmentvariables-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-environmentvariables-list"),
        )

    def test_unauthed_projects_environmentvariables_detail(self):
        response = self.client.get(
            reverse(
                "projects-environmentvariables-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "environmentvariable_pk": self.environmentvariable.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 401)

    def test_projects_environmentvariables_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(
            reverse(
                "projects-environmentvariables-detail",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                    "environmentvariable_pk": self.environmentvariable.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-environmentvariables-detail"),
        )

    def test_unauthed_projects_environmentvariables_list_post(self):
        data = {}

        response = self.client.post(
            reverse(
                "projects-environmentvariables-list",
                kwargs={
                    "parent_lookup_project__slug": self.others_project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            reverse(
                "projects-environmentvariables-list",
                kwargs={
                    "parent_lookup_project__slug": self.others_project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 403)

    def test_projects_environmentvariables_list_post(self):
        self.assertEqual(self.project.environmentvariable_set.count(), 1)
        data = {
            "name": "NEWENVVAR",
            "value": "c3b2a1",
            "public": True,
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            reverse(
                "projects-environmentvariables-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(self.project.environmentvariable_set.count(), 2)
        self.assertEqual(response.status_code, 201)

        environmentvariable = self.project.environmentvariable_set.get(name="NEWENVVAR")
        self.assertEqual(environmentvariable.value, "c3b2a1")

        response_json = response.json()
        response_json["created"] = "2019-04-29T10:00:00Z"
        response_json["modified"] = "2019-04-29T12:00:00Z"
        self.assertDictEqual(
            response_json,
            self._get_response_dict("projects-environmentvariables-list_POST"),
        )

    def test_projects_environmentvariables_detail_delete(self):
        url = reverse(
            "projects-environmentvariables-detail",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
                "environmentvariable_pk": self.environmentvariable.pk,
            },
        )
        self.client.logout()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

        self.assertEqual(self.project.environmentvariable_set.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.project.environmentvariable_set.count(), 0)

    def test_create_large_environment_variable(self):
        url = reverse(
            "projects-environmentvariables-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        resp = self.client.post(
            url,
            data={"name": "NEWENVVAR", "value": "a" * (48000 + 1), "public": True},
        )
        assert resp.status_code == 400
        assert resp.data == {
            "value": ["Ensure this field has no more than 48000 characters."]
        }

    def test_environment_variables_total_size_per_project(self):
        size = 2000
        for i in range((MAX_SIZE_ENV_VARS_PER_PROJECT - size) // size):
            get(
                EnvironmentVariable,
                project=self.project,
                name=f"ENVVAR{i}",
                value="a" * size,
                public=False,
            )

        url = reverse(
            "projects-environmentvariables-list",
            kwargs={
                "parent_lookup_project__slug": self.project.slug,
            },
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        resp = self.client.post(
            url,
            data={"name": "A", "value": "a" * (size // 2), "public": True},
        )
        assert resp.status_code == 201

        resp = self.client.post(
            url,
            data={"name": "B", "value": "a" * size, "public": True},
        )
        assert resp.status_code == 400
        assert resp.json() == [
            "The total size of all environment variables in the project cannot exceed 256 KB."
        ]

    def test_create_environment_variable_with_public_flag(self):
        self.assertEqual(self.project.environmentvariable_set.count(), 1)
        data = {
            "name": "TEST_ENV_VAR",
            "value": "test_value",
            "public": True,
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            reverse(
                "projects-environmentvariables-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.environmentvariable_set.count(), 2)

        env_var = self.project.environmentvariable_set.get(name="TEST_ENV_VAR")
        self.assertEqual(env_var.value, "test_value")
        self.assertTrue(env_var.public)

    def test_create_environment_variable_without_public_flag(self):
        self.assertEqual(self.project.environmentvariable_set.count(), 1)
        data = {
            "name": "TEST_ENV_VAR",
            "value": "test_value",
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(
            reverse(
                "projects-environmentvariables-list",
                kwargs={
                    "parent_lookup_project__slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.environmentvariable_set.count(), 2)

        env_var = self.project.environmentvariable_set.get(name="TEST_ENV_VAR")
        self.assertEqual(env_var.value, "test_value")
        self.assertFalse(env_var.public)
