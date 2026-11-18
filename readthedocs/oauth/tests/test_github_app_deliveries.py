from io import StringIO

import pytest
import requests_mock
from django.core.management import CommandError
from django.core.management import call_command
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import GitHubAccountType
from readthedocs.oauth.models import GitHubAppInstallation
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.models import Project


API_URL = "https://api.github.com:443"


def delivery(id, repository_id, action="opened"):
    return {
        "id": id,
        "guid": f"guid-{id}",
        "delivered_at": f"2026-11-18T05:00:0{id}Z",
        "status_code": 200,
        "event": "pull_request",
        "action": action,
        "installation_id": 1111,
        "repository_id": repository_id,
    }


class TestGitHubAppDeliveriesCommand(TestCase):
    def setUp(self):
        installation = get(
            GitHubAppInstallation,
            installation_id=1111,
            target_id=1111,
            target_type=GitHubAccountType.USER,
        )
        remote_repository = get(
            RemoteRepository,
            remote_id="1234",
            vcs_provider=GITHUB_APP,
            github_app_installation=installation,
        )
        self.project = get(Project, slug="project", remote_repository=remote_repository)

    @requests_mock.Mocker(kw="request")
    def test_list_deliveries_for_project(self, request):
        next_url = "https://api.github.com/app/hook/deliveries?per_page=100&cursor=abc"
        request.get(
            f"{API_URL}/app/hook/deliveries?per_page=100",
            json=[delivery(1, 1234), delivery(2, 9999)],
            headers={"Link": f'<{next_url}>; rel="next"'},
            complete_qs=True,
        )
        request.get(
            f"{API_URL}/app/hook/deliveries?per_page=100&cursor=abc",
            json=[delivery(3, 1234, action="closed")],
            complete_qs=True,
        )

        out = StringIO()
        call_command("github_app_deliveries", self.project.slug, stdout=out)

        assert out.getvalue().splitlines() == [
            "2026-11-18T05:00:01Z  1  200  pull_request opened  guid-1",
            "2026-11-18T05:00:03Z  3  200  pull_request closed  guid-3",
            "Searched deliveries back to 2026-11-18T05:00:03Z.",
        ]

    def test_project_not_connected_to_github_app(self):
        project = get(Project, slug="other")
        with pytest.raises(CommandError):
            call_command("github_app_deliveries", project.slug)

    @requests_mock.Mocker(kw="request")
    def test_redeliver(self, request):
        redeliver = request.post(f"{API_URL}/app/hook/deliveries/3/attempts", status_code=202, json={})
        call_command("github_app_deliveries", self.project.slug, redeliver=3, stdout=StringIO())
        assert redeliver.called
