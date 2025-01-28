from django.test import override_settings
from django.urls import reverse

from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import Project

from .mixins import APIEndpointMixin


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=False,
    ALLOW_PRIVATE_REPOS=False,
)
class SubprojectsEndpointTests(APIEndpointMixin):
    def setUp(self):
        super().setUp()
        self._create_subproject()

    def test_projects_subprojects_list_anonymous_user(self):
        url = reverse(
            "projects-subprojects-list",
            kwargs={
                "parent_lookup_parent__slug": self.project.slug,
            },
        )
        expected_response = self._get_response_dict("projects-subprojects-list")
        empty_response = self._get_response_dict("projects-list-empty")

        # Subproject is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Subproject is private
        Project.objects.filter(slug=self.subproject.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), empty_response)

    def test_projects_subprojects_list(self):
        url = reverse(
            "projects-subprojects-list",
            kwargs={
                "parent_lookup_parent__slug": self.project.slug,
            },
        )
        expected_response = self._get_response_dict("projects-subprojects-list")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Subproject is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Subproject is private
        Project.objects.filter(slug=self.subproject.slug).update(privacy_level=PRIVATE)
        expected_response["results"][0]["child"]["privacy_level"] = PRIVATE
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_subprojects_list_other_user(self):
        url = reverse(
            "projects-subprojects-list",
            kwargs={
                "parent_lookup_parent__slug": self.project.slug,
            },
        )
        expected_response = self._get_response_dict("projects-subprojects-list")
        empty_response = self._get_response_dict("projects-list-empty")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # Subproject is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Subproject is private
        Project.objects.filter(slug=self.subproject.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), empty_response)

    def test_projects_subprojects_detail_anonymous_user(self):
        url = reverse(
            "projects-subprojects-detail",
            kwargs={
                "parent_lookup_parent__slug": self.project.slug,
                "alias_slug": self.project_relationship.alias,
            },
        )
        expected_response = self._get_response_dict("projects-subprojects-detail")

        # Subproject is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Subproject is private
        Project.objects.filter(slug=self.subproject.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_projects_subprojects_detail(self):
        url = reverse(
            "projects-subprojects-detail",
            kwargs={
                "parent_lookup_parent__slug": self.project.slug,
                "alias_slug": self.project_relationship.alias,
            },
        )
        expected_response = self._get_response_dict("projects-subprojects-detail")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Subproject is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Subproject is private
        Project.objects.filter(slug=self.subproject.slug).update(privacy_level=PRIVATE)
        expected_response["child"]["privacy_level"] = PRIVATE
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

    def test_projects_subprojects_detail_other_user(self):
        url = reverse(
            "projects-subprojects-detail",
            kwargs={
                "parent_lookup_parent__slug": self.project.slug,
                "alias_slug": self.project_relationship.alias,
            },
        )
        expected_response = self._get_response_dict("projects-subprojects-detail")

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")

        # Subproject is public
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected_response)

        # Subproject is private
        Project.objects.filter(slug=self.subproject.slug).update(privacy_level=PRIVATE)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_projects_subprojects_list_post(self):
        newproject = self._create_new_project()
        self.organization.projects.add(newproject)

        self.assertEqual(self.project.subprojects.count(), 1)
        url = reverse(
            "projects-subprojects-list",
            kwargs={
                "parent_lookup_parent__slug": self.project.slug,
            },
        )
        data = {
            "child": newproject.slug,
            "alias": "subproject-alias",
        }

        self.client.logout()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.subprojects.count(), 2)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict("projects-subprojects-list_POST"),
        )

    def test_projects_subprojects_list_post_with_others_as_child(self):
        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "child": self.others_project.slug,
            "alias": "subproject-alias",
        }
        response = self.client.post(
            reverse(
                "projects-subprojects-list",
                kwargs={
                    "parent_lookup_parent__slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.project.subprojects.count(), 1)

    def test_projects_subprojects_list_post_with_subproject_of_itself(self):
        newproject = self._create_new_project()
        self.assertEqual(newproject.subprojects.count(), 0)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "child": newproject.slug,
            "alias": "subproject-alias",
        }
        response = self.client.post(
            reverse(
                "projects-subprojects-list",
                kwargs={
                    "parent_lookup_parent__slug": newproject.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Project with slug=new-project is not valid as subproject",
            response.json()["child"][0],
        )
        self.assertEqual(newproject.subprojects.count(), 0)

    def test_projects_subprojects_list_post_with_child_already_superproject(self):
        newproject = self._create_new_project()
        self.assertEqual(newproject.subprojects.count(), 0)
        self.assertTrue(self.project.subprojects.exists())
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "child": self.project.slug,
            "alias": "subproject-alias",
        }
        response = self.client.post(
            reverse(
                "projects-subprojects-list",
                kwargs={
                    "parent_lookup_parent__slug": newproject.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Project with slug=project is not valid as subproject",
            response.json()["child"][0],
        )
        self.assertEqual(newproject.subprojects.count(), 0)

    def test_projects_subprojects_list_post_with_child_already_subproject(self):
        newproject = self._create_new_project()
        self.assertEqual(newproject.subprojects.count(), 0)
        self.assertTrue(self.subproject.superprojects.exists())
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "child": self.subproject.slug,
            "alias": "subproject-alias",
        }
        response = self.client.post(
            reverse(
                "projects-subprojects-list",
                kwargs={
                    "parent_lookup_parent__slug": newproject.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Project with slug=subproject is not valid as subproject",
            response.json()["child"][0],
        )
        self.assertEqual(newproject.subprojects.count(), 0)

    def test_projects_subprojects_list_post_nested_subproject(self):
        newproject = self._create_new_project()
        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "child": newproject.slug,
            "alias": "subproject-alias",
        }
        response = self.client.post(
            reverse(
                "projects-subprojects-list",
                kwargs={
                    "parent_lookup_parent__slug": self.subproject.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Subproject nesting is not supported",
            response.json()["non_field_errors"],
        )
        self.assertEqual(self.project.subprojects.count(), 1)

    def test_projects_subprojects_list_post_unique_alias(self):
        newproject = self._create_new_project()
        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "child": newproject.slug,
            "alias": "subproject",  # this alias is already set for another subproject
        }
        response = self.client.post(
            reverse(
                "projects-subprojects-list",
                kwargs={
                    "parent_lookup_parent__slug": self.project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "A subproject with this alias already exists",
            response.json()["alias"],
        )
        self.assertEqual(self.project.subprojects.count(), 1)

    def test_projects_subprojects_list_post_with_others_as_parent(self):
        self.assertEqual(self.others_project.subprojects.count(), 0)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        data = {
            "child": self.project.slug,
            "alias": "subproject-alias",
        }
        response = self.client.post(
            reverse(
                "projects-subprojects-list",
                kwargs={
                    "parent_lookup_parent__slug": self.others_project.slug,
                },
            ),
            data,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.others_project.subprojects.count(), 0)

    def test_projects_subprojects_detail_delete(self):
        url = reverse(
            "projects-subprojects-detail",
            kwargs={
                "parent_lookup_parent__slug": self.project.slug,
                "alias_slug": self.project_relationship.alias,
            },
        )
        self.client.logout()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

        self.assertEqual(self.project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.project.subprojects.count(), 0)

    def test_projects_subprojects_detail_delete_others_project(self):
        newproject = self._create_new_project()
        project_relationship = self.others_project.add_subproject(newproject)
        self.assertEqual(self.others_project.subprojects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.delete(
            reverse(
                "projects-subprojects-detail",
                kwargs={
                    "parent_lookup_parent__slug": self.others_project.slug,
                    "alias_slug": project_relationship.alias,
                },
            ),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.project.subprojects.count(), 1)
