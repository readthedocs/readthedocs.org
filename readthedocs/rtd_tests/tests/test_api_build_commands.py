import datetime

from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get
from rest_framework import status
from rest_framework.test import APIClient

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.builds.models import Build
from readthedocs.projects.models import Project


class APIBuildCommandTests(TestCase):
    fixtures = ["eric.json", "test_data.json"]

    def setUp(self):
        self.project = Project.objects.get(pk=1)
        self.version = self.project.versions.first()

    def test_build_detail_exposes_build_job(self):
        _, build_api_key = BuildAPIKey.objects.create_key(self.project)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {build_api_key}")

        build = get(Build, project=self.project, version=self.version, success=True)
        now = timezone.now()

        response = client.post(
            "/api/v2/command/",
            {
                "build": build.pk,
                "command": "python -m sphinx",
                "build_job": "build.html",
                "start_time": now - datetime.timedelta(seconds=3),
                "end_time": now,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        detail = client.get(f"/api/v2/build/{build.pk}/")
        assert detail.status_code == status.HTTP_200_OK
        assert detail.data["commands"][0]["job"] == "build.html"
        assert detail.data["commands"][0]["build_job"] == "build.html"
