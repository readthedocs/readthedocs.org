import json
from unittest import mock

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.api.v2.views.integrations import (
    GITHUB_EVENT_HEADER,
    GITHUB_SIGNATURE_HEADER,
    WebhookMixin,
)
from readthedocs.builds.constants import (
    BRANCH,
    EXTERNAL,
    EXTERNAL_VERSION_STATE_CLOSED,
    EXTERNAL_VERSION_STATE_OPEN,
    LATEST,
    TAG,
)
from readthedocs.builds.models import Version
from readthedocs.oauth.models import (
    GitHubAccountType,
    GitHubAppInstallation,
    RemoteOrganization,
    RemoteRepository,
)
from readthedocs.oauth.services import GitHubAppService
from readthedocs.projects.models import Project


def get_signature(payload):
    if not isinstance(payload, str):
        payload = json.dumps(payload)
    return "sha256=" + WebhookMixin.get_digest(
        secret=settings.GITHUB_APP_WEBHOOK_SECRET,
        msg=payload,
    )


class TestGitHubAppWebhook(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user], default_branch="main")
        self.version_latest = self.project.versions.get(slug=LATEST)
        self.version = get(
            Version, project=self.project, verbose_name="1.0", type=BRANCH, active=True
        )
        self.version_main = get(
            Version, project=self.project, verbose_name="main", type=BRANCH, active=True
        )
        self.version_tag = get(
            Version, project=self.project, verbose_name="2.0", type=TAG, active=True
        )
        self.socialaccount = get(
            SocialAccount, user=self.user, provider=GitHubAppProvider.id
        )
        self.installation = get(
            GitHubAppInstallation,
            installation_id=1111,
            target_id=1111,
            target_type=GitHubAccountType.USER,
        )

        self.remote_repository = get(
            RemoteRepository,
            remote_id="1234",
            name="repo",
            full_name="user/repo",
            vcs_provider=GitHubAppProvider.id,
            github_app_installation=self.installation,
        )
        self.project.remote_repository = self.remote_repository
        self.project.save()
        self.url = reverse("github_app_webhook")

    def post_webhook(self, event, payload):
        headers = {
            GITHUB_EVENT_HEADER: event,
            GITHUB_SIGNATURE_HEADER: get_signature(payload),
        }
        return self.client.post(
            self.url, data=payload, content_type="application/json", headers=headers
        )

    @mock.patch.object(GitHubAppService, "sync")
    def test_installation_created(self, sync):
        new_installation_id = 2222
        assert not GitHubAppInstallation.objects.filter(
            installation_id=new_installation_id
        ).exists()
        payload = {
            "action": "created",
            "installation": {
                "id": new_installation_id,
                "target_id": 2222,
                "target_type": GitHubAccountType.USER,
            },
        }
        r = self.post_webhook("installation", payload)
        assert r.status_code == 200

        installation = GitHubAppInstallation.objects.get(
            installation_id=new_installation_id
        )
        assert installation.target_id == 2222
        assert installation.target_type == GitHubAccountType.USER
        sync.assert_called_once()

    @mock.patch.object(GitHubAppService, "sync")
    def test_installation_created_with_existing_installation(self, sync):
        paylod = {
            "action": "created",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
        }
        r = self.post_webhook("installation", paylod)
        assert r.status_code == 200
        sync.assert_called_once()
        self.installation.refresh_from_db()
        assert self.installation.target_id == 1111
        assert self.installation.target_type == GitHubAccountType.USER
        assert GitHubAppInstallation.objects.count() == 1

    @mock.patch.object(GitHubAppService, "sync")
    def test_installation_unsuspended(self, sync):
        new_installation_id = 2222
        assert GitHubAppInstallation.objects.count() == 1
        assert not GitHubAppInstallation.objects.filter(
            installation_id=new_installation_id
        ).exists()
        payload = {
            "action": "unsuspended",
            "installation": {
                "id": new_installation_id,
                "target_id": 2222,
                "target_type": GitHubAccountType.USER,
            },
        }
        r = self.post_webhook("installation", payload)
        assert r.status_code == 200

        installation = GitHubAppInstallation.objects.get(
            installation_id=new_installation_id
        )
        assert installation.target_id == 2222
        assert installation.target_type == GitHubAccountType.USER
        sync.assert_called_once()
        assert GitHubAppInstallation.objects.count() == 2

    @mock.patch.object(GitHubAppService, "sync")
    def test_installation_unsuspended_with_existing_installation(self, sync):
        paylod = {
            "action": "unsuspended",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
        }
        r = self.post_webhook("installation", paylod)
        assert r.status_code == 200
        sync.assert_called_once()
        self.installation.refresh_from_db()
        assert self.installation.target_id == 1111
        assert self.installation.target_type == GitHubAccountType.USER
        assert GitHubAppInstallation.objects.count() == 1

    def test_installation_deleted(self):
        payload = {
            "action": "deleted",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
        }
        r = self.post_webhook("installation", payload)
        assert r.status_code == 200
        assert not GitHubAppInstallation.objects.filter(
            installation_id=self.installation.installation_id
        ).exists()

    def test_installation_deleted_with_non_existing_installation(self):
        install_id = 2222
        assert not GitHubAppInstallation.objects.filter(
            installation_id=install_id
        ).exists()
        payload = {
            "action": "deleted",
            "installation": {
                "id": install_id,
                "target_id": 2222,
                "target_type": GitHubAccountType.USER,
            },
        }
        r = self.post_webhook("installation", payload)
        assert r.status_code == 200
        assert not GitHubAppInstallation.objects.filter(installation_id=2222).exists()

    def test_installation_suspended(self):
        assert GitHubAppInstallation.objects.filter(
            installation_id=self.installation.installation_id
        ).exists()
        payload = {
            "action": "suspended",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
        }
        r = self.post_webhook("installation", payload)
        assert r.status_code == 200
        assert not GitHubAppInstallation.objects.filter(
            installation_id=self.installation.installation_id
        ).exists()

    def test_installation_suspended_with_non_existing_installation(self):
        install_id = 2222
        assert not GitHubAppInstallation.objects.filter(
            installation_id=install_id
        ).exists()
        payload = {
            "action": "suspended",
            "installation": {
                "id": install_id,
                "target_id": 2222,
                "target_type": GitHubAccountType.USER,
            },
        }
        r = self.post_webhook("installation", payload)
        assert r.status_code == 200
        assert not GitHubAppInstallation.objects.filter(installation_id=2222).exists()

    def test_installation_new_permissions_accepted(self):
        payload = {
            "action": "new_permissions_accepted",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
        }
        r = self.post_webhook("installation", payload)
        assert r.status_code == 200

    @mock.patch.object(GitHubAppService, "update_or_create_repositories")
    def test_installation_repositories_added(self, update_or_create_repositories):
        payload = {
            "action": "added",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "repository_selection": "selected",
            "repositories_added": [
                {
                    "id": 1234,
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "private": False,
                },
                {
                    "id": 5678,
                    "name": "repo2",
                    "full_name": "user/repo2",
                    "private": True,
                },
            ],
        }
        r = self.post_webhook("installation_repositories", payload)
        assert r.status_code == 200
        update_or_create_repositories.assert_called_once_with([1234, 5678])

    @mock.patch.object(GitHubAppService, "sync")
    def test_installation_repositories_added_all(self, sync):
        payload = {
            "action": "added",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "repository_selection": "all",
        }
        r = self.post_webhook("installation_repositories", payload)
        assert r.status_code == 200
        sync.assert_called_once()

    def test_installation_repositories_removed(self):
        assert self.installation.repositories.count() == 1
        payload = {
            "action": "removed",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "repository_selection": "selected",
            "repositories_removed": [
                {
                    "id": 1234,
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "private": False,
                },
                {
                    "id": 5678,
                    "name": "repo2",
                    "full_name": "user/repo2",
                    "private": True,
                },
            ],
        }
        r = self.post_webhook("installation_repositories", payload)
        assert r.status_code == 200
        assert self.installation.repositories.count() == 0

    @mock.patch.object(GitHubAppService, "sync")
    def test_installation_target(self, sync):
        payload = {
            "action": "renamed",
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
        }
        r = self.post_webhook("installation_target", payload)
        assert r.status_code == 200
        sync.assert_called_once()

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_push_branch_created(self, sync_repository_task):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "created": True,
            "deleted": False,
            "ref": "refs/heads/branch",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("push", payload)
        assert r.status_code == 200
        sync_repository_task.apply_async.assert_called_once_with(
            args=[self.version_latest.pk],
            kwargs={"build_api_key": mock.ANY},
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_push_tag_created(self, sync_repository_task):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "created": True,
            "deleted": False,
            "ref": "refs/tags/tag",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("push", payload)
        assert r.status_code == 200
        sync_repository_task.apply_async.assert_called_once_with(
            args=[self.version_latest.pk],
            kwargs={"build_api_key": mock.ANY},
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_push_branch_deleted(self, sync_repository_task):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "created": False,
            "deleted": True,
            "ref": "refs/heads/branch",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("push", payload)
        assert r.status_code == 200
        sync_repository_task.apply_async.assert_called_once_with(
            args=[self.version_latest.pk],
            kwargs={"build_api_key": mock.ANY},
        )

    @mock.patch("readthedocs.core.views.hooks.sync_repository_task")
    def test_push_tag_deleted(self, sync_repository_task):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "created": False,
            "deleted": True,
            "ref": "refs/tags/tag",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("push", payload)
        assert r.status_code == 200
        sync_repository_task.apply_async.assert_called_once_with(
            args=[self.version_latest.pk],
            kwargs={"build_api_key": mock.ANY},
        )

    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_push_branch(self, trigger_build):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "created": False,
            "deleted": False,
            "ref": "refs/heads/main",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("push", payload)
        assert r.status_code == 200
        trigger_build.assert_has_calls(
            [
                mock.call(project=self.project, version=self.version_main),
                mock.call(project=self.project, version=self.version_latest),
            ]
        )

    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_push_tag(self, trigger_build):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "created": False,
            "deleted": False,
            "ref": "refs/tags/2.0",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("push", payload)
        assert r.status_code == 200
        trigger_build.assert_called_once_with(
            project=self.project,
            version=self.version_tag,
        )

    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_pull_request_opened(self, trigger_build):
        self.project.external_builds_enabled = True
        self.project.save()
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "opened",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200
        external_version = self.project.versions.get(verbose_name="1", type=EXTERNAL)
        assert external_version.identifier == "1234abcd"
        assert external_version.state == EXTERNAL_VERSION_STATE_OPEN
        assert external_version.active
        trigger_build.assert_called_once_with(
            project=self.project,
            version=external_version,
            commit=external_version.identifier,
        )

    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_pull_request_opened_pr_previews_disabled(self, trigger_build):
        self.project.external_builds_enabled = False
        self.project.save()
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "opened",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200
        assert not self.project.versions.filter(verbose_name="1", type=EXTERNAL).exists()
        trigger_build.assert_not_called()

    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_pull_request_reopened(self, trigger_build):
        self.project.external_builds_enabled = True
        self.project.save()
        external_version = get(
            Version,
            project=self.project,
            verbose_name="1",
            type=EXTERNAL,
            active=True,
            identifier="1234changeme",
            state=EXTERNAL_VERSION_STATE_CLOSED,
        )
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "reopened",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200

        external_version.refresh_from_db()
        assert external_version.identifier == "1234abcd"
        assert external_version.state == EXTERNAL_VERSION_STATE_OPEN
        assert external_version.active
        trigger_build.assert_called_once_with(
            project=self.project,
            version=external_version,
            commit=external_version.identifier,
        )

    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_pull_request_reopened_pr_previews_disabled(self, trigger_build):
        self.project.external_builds_enabled = False
        self.project.save()
        external_version = get(
            Version,
            project=self.project,
            verbose_name="1",
            type=EXTERNAL,
            active=True,
            identifier="1234changeme",
            state=EXTERNAL_VERSION_STATE_CLOSED,
        )
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "reopened",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200

        external_version.refresh_from_db()
        assert external_version.identifier == "1234changeme"
        assert external_version.state == EXTERNAL_VERSION_STATE_CLOSED
        assert external_version.active
        trigger_build.assert_not_called()

    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_pull_request_synchronize(self, trigger_build):
        self.project.external_builds_enabled = True
        self.project.save()
        external_version = get(
            Version,
            project=self.project,
            verbose_name="1",
            type=EXTERNAL,
            active=True,
            identifier="1234changeme",
        )
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "synchronize",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200

        external_version.refresh_from_db()
        assert external_version.identifier == "1234abcd"
        assert external_version.state == EXTERNAL_VERSION_STATE_OPEN
        assert external_version.active
        trigger_build.assert_called_once_with(
            project=self.project,
            version=external_version,
            commit=external_version.identifier,
        )

    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_pull_request_synchronize_pr_previews_disabled(self, trigger_build):
        self.project.external_builds_enabled = False
        self.project.save()
        external_version = get(
            Version,
            project=self.project,
            verbose_name="1",
            type=EXTERNAL,
            active=True,
            identifier="1234changeme",
            state=EXTERNAL_VERSION_STATE_OPEN,
        )
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "synchronize",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200

        external_version.refresh_from_db()
        assert external_version.identifier == "1234changeme"
        assert external_version.state == EXTERNAL_VERSION_STATE_OPEN
        assert external_version.active
        trigger_build.assert_not_called()

    def test_pull_request_closed(self):
        self.project.external_builds_enabled = True
        self.project.save()
        external_version = get(
            Version,
            project=self.project,
            verbose_name="1",
            type=EXTERNAL,
            active=True,
            identifier="1234abcd",
        )
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "closed",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200

        external_version.refresh_from_db()
        assert external_version.identifier == "1234abcd"
        assert external_version.state == EXTERNAL_VERSION_STATE_CLOSED
        assert external_version.active

    def test_pull_request_closed_pr_previews_disabled(self):
        self.project.external_builds_enabled = False
        self.project.save()
        external_version = get(
            Version,
            project=self.project,
            verbose_name="1",
            type=EXTERNAL,
            active=True,
            identifier="1234abcd",
        )
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "closed",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200

        external_version.refresh_from_db()
        assert external_version.identifier == "1234abcd"
        assert external_version.state == EXTERNAL_VERSION_STATE_CLOSED
        assert external_version.active

    def test_pull_request_edited(self):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "edited",
            "pull_request": {
                "number": 1,
                "head": {
                    "ref": "new-feature",
                    "sha": "1234abcd",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("pull_request", payload)
        assert r.status_code == 200

    @mock.patch.object(GitHubAppService, "update_or_create_repositories")
    def test_repository_edited(self, update_or_create_repositories):
        actions = ["edited", "renamed", "transferred", "privatized", "publicized"]
        for action in actions:
            update_or_create_repositories.reset_mock()
            payload = {
                "installation": {
                    "id": self.installation.installation_id,
                    "target_id": self.installation.target_id,
                    "target_type": self.installation.target_type,
                },
                "action": action,
                "changes": {},
                "repository": {
                    "id": self.remote_repository.remote_id,
                    "full_name": self.remote_repository.full_name,
                },
            }
            r = self.post_webhook("repository", payload)
            assert r.status_code == 200
            update_or_create_repositories.assert_called_once_with(
                [self.remote_repository.remote_id]
            )

    def test_repository_created(self):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "created",
            "repository": {
                "id": 5678,
                "full_name": "user/repo2",
            },
        }
        r = self.post_webhook("repository", payload)
        assert r.status_code == 200

    @mock.patch.object(GitHubAppService, "sync")
    def test_organization_member_added(self, sync):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "member_added",
        }
        r = self.post_webhook("organization", payload)
        assert r.status_code == 200
        sync.assert_called_once()

    @mock.patch.object(GitHubAppService, "sync")
    def test_organization_member_removed(self, sync):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "member_removed",
        }
        r = self.post_webhook("organization", payload)
        assert r.status_code == 200
        sync.assert_called_once()

    @mock.patch.object(GitHubAppService, "sync")
    def test_organization_renamed(self, sync):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "renamed",
        }
        r = self.post_webhook("organization", payload)
        assert r.status_code == 200
        sync.assert_called_once()

    def test_organization_deleted(self):
        organization_id = 1234
        get(
            RemoteOrganization,
            remote_id=str(organization_id),
            name="org",
            vcs_provider=GitHubAppProvider.id,
        )
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "deleted",
            "organization": {
                "id": organization_id,
                "login": "org",
            },
        }
        r = self.post_webhook("organization", payload)
        assert r.status_code == 200
        assert not RemoteOrganization.objects.filter(
            remote_id=str(organization_id)
        ).exists()

    def test_organization_member_invited(self):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "member_invited",
        }
        r = self.post_webhook("organization", payload)
        assert r.status_code == 200

    @mock.patch.object(GitHubAppService, "update_or_create_repositories")
    def test_member_added(self, update_or_create_repositories):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "added",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("member", payload)
        assert r.status_code == 200
        update_or_create_repositories.assert_called_once_with(
            [self.remote_repository.remote_id]
        )

    @mock.patch.object(GitHubAppService, "update_or_create_repositories")
    def test_member_edited(self, update_or_create_repositories):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "edited",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("member", payload)
        assert r.status_code == 200
        update_or_create_repositories.assert_called_once_with(
            [self.remote_repository.remote_id]
        )

    @mock.patch.object(GitHubAppService, "update_or_create_repositories")
    def test_member_removed(self, update_or_create_repositories):
        payload = {
            "installation": {
                "id": self.installation.installation_id,
                "target_id": self.installation.target_id,
                "target_type": self.installation.target_type,
            },
            "action": "removed",
            "repository": {
                "id": self.remote_repository.remote_id,
                "full_name": self.remote_repository.full_name,
            },
        }
        r = self.post_webhook("member", payload)
        assert r.status_code == 200
        update_or_create_repositories.assert_called_once_with(
            [self.remote_repository.remote_id]
        )

    def test_github_app_authorization(self):
        payload = {
            "action": "revoked",
            "sender": {
                "login": "user",
            },
        }
        r = self.post_webhook("github_app_authorization", payload)
        assert r.status_code == 200
