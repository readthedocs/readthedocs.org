"""OAuth utility functions."""

import json
import re

import structlog
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from requests.exceptions import HTTPError
from requests.exceptions import RequestException

from readthedocs.builds import utils as build_utils
from readthedocs.builds.constants import BUILD_STATUS_SUCCESS
from readthedocs.builds.constants import SELECT_BUILD_STATUS
from readthedocs.integrations.models import Integration

from ..constants import GITHUB
from ..models import RemoteOrganization
from ..models import RemoteRepository
from .base import SyncServiceError
from .base import UserService


log = structlog.get_logger(__name__)


class GitHubService(UserService):
    """Provider service for GitHub."""

    vcs_provider_slug = GITHUB
    allauth_provider = GitHubProvider
    base_api_url = "https://api.github.com"
    # TODO replace this with a less naive check
    url_pattern = re.compile(r"github\.com")
    supports_build_status = True

    def sync_repositories(self):
        """Sync repositories from GitHub API."""
        remote_ids = []

        try:
            repos = self.paginate(f"{self.base_api_url}/user/repos", per_page=100)
            for repo in repos:
                remote_repository = self.create_repository(repo)
                if remote_repository:
                    remote_ids.append(remote_repository.remote_id)
        except (TypeError, ValueError):
            log.warning("Error syncing GitHub repositories")
            raise SyncServiceError(
                SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                    provider=self.vcs_provider_slug
                )
            )
        return remote_ids

    def sync_organizations(self):
        """
        Sync organizations from GitHub API.

        This method only creates the relationships between the
        organizations and the user, as all the repositories
        are already created in the sync_repositories method.
        """
        organization_remote_ids = []

        try:
            orgs = self.paginate(f"{self.base_api_url}/user/orgs", per_page=100)
            for org in orgs:
                org_details = self.session.get(org["url"]).json()
                remote_organization = self.create_organization(org_details)
                remote_organization.get_remote_organization_relation(self.user, self.account)
                organization_remote_ids.append(remote_organization.remote_id)
        except (TypeError, ValueError):
            log.warning("Error syncing GitHub organizations")
            raise SyncServiceError(
                SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                    provider=self.allauth_provider.name
                )
            )

        return organization_remote_ids, []

    def _has_access_to_repository(self, fields):
        """Check if the user has access to the repository, and if they are an admin."""
        permissions = fields.get("permissions", {})
        # If the repo is public, the user can still access it,
        # so we need to check if the user has any access
        # to the repository, even if they are not an admin.
        has_access = any(
            permissions.get(key, False) for key in ["admin", "maintain", "push", "triage"]
        )
        is_admin = permissions.get("admin", False)
        return has_access, is_admin

    def update_repository(self, remote_repository: RemoteRepository):
        resp = self.session.get(f"{self.base_api_url}/repositories/{remote_repository.remote_id}")

        # The repo was deleted, or the user does not have access to it.
        # In any case, we remove the user relationship.
        if resp.status_code in [403, 404]:
            log.info(
                "User no longer has access to the repository, removing remote relationship.",
                remote_repository=remote_repository.remote_id,
            )
            remote_repository.get_remote_repository_relation(self.user, self.account).delete()
            return

        if resp.status_code != 200:
            log.warning(
                "Error fetching repository from GitHub",
                remote_repository=remote_repository.remote_id,
                status_code=resp.status_code,
            )
            return

        data = resp.json()
        self._update_repository_from_fields(remote_repository, data)

        has_access, is_admin = self._has_access_to_repository(data)
        relation = remote_repository.get_remote_repository_relation(
            self.user,
            self.account,
        )
        if not has_access:
            # If the user no longer has access to the repository,
            # we remove the remote relationship.
            log.info(
                "User no longer has access to the repository, removing remote relationship.",
                remote_repository=remote_repository.remote_id,
            )
            relation.delete()
        else:
            relation.admin = is_admin
            relation.save()

    def create_repository(self, fields, privacy=None):
        """
        Update or create a repository from GitHub API response.

        :param fields: dictionary of response data from API
        :param privacy: privacy level to support
        :rtype: RemoteRepository
        """
        privacy = privacy or settings.DEFAULT_PRIVACY_LEVEL
        if any(
            [
                (privacy == "private"),
                (fields["private"] is False and privacy == "public"),
            ]
        ):
            repo, _ = RemoteRepository.objects.get_or_create(
                remote_id=str(fields["id"]),
                vcs_provider=self.vcs_provider_slug,
            )
            self._update_repository_from_fields(repo, fields)

            remote_repository_relation = repo.get_remote_repository_relation(
                self.user, self.account
            )
            _, is_admin = self._has_access_to_repository(fields)
            remote_repository_relation.admin = is_admin
            remote_repository_relation.save()

            return repo

        log.debug(
            "Not importing repository because mismatched type.",
            repository=fields["name"],
        )

    def _update_repository_from_fields(self, repo, fields):
        owner_type = fields["owner"]["type"]
        organization = None
        if owner_type == "Organization":
            organization = self.create_organization(fields=fields["owner"])

        # If there is an organization associated with this repository,
        # attach the organization to the repository.
        if organization and owner_type == "Organization":
            repo.organization = organization

        # If the repository belongs to a user,
        # remove the organization linked to the repository.
        if owner_type == "User":
            repo.organization = None

        repo.name = fields["name"]
        repo.full_name = fields["full_name"]
        repo.description = fields["description"]
        repo.ssh_url = fields["ssh_url"]
        repo.html_url = fields["html_url"]
        repo.private = fields["private"]
        repo.vcs = "git"
        repo.avatar_url = fields.get("owner", {}).get("avatar_url")
        repo.default_branch = fields.get("default_branch")

        if repo.private:
            repo.clone_url = fields["ssh_url"]
        else:
            repo.clone_url = fields["clone_url"]

        if not repo.avatar_url:
            repo.avatar_url = self.default_user_avatar_url

        repo.save()

    def create_organization(self, fields):
        """
        Update or create remote organization from GitHub API response.

        :param fields: dictionary response of data from API
        :param bool create_relationship: Whether to create a remote relationship between the
         organization and the current user. If `False`, only the `RemoteOrganization` object
         will be created/updated.
        :rtype: RemoteOrganization

        .. note::

           This method caches organizations by their remote ID to avoid
           unnecessary database queries, specially when creating
           multiple repositories that belong to the same organization.
        """
        organization_id = str(fields["id"])
        if organization_id in self._organizations_cache:
            return self._organizations_cache[organization_id]

        organization, _ = RemoteOrganization.objects.get_or_create(
            remote_id=organization_id,
            vcs_provider=self.vcs_provider_slug,
        )

        organization.url = fields.get("html_url")
        # fields['login'] contains GitHub Organization slug
        organization.slug = fields.get("login")
        organization.name = fields.get("name")
        organization.email = fields.get("email")
        organization.avatar_url = fields.get("avatar_url")

        if not organization.avatar_url:
            organization.avatar_url = self.default_org_avatar_url

        organization.save()

        self._organizations_cache[organization_id] = organization
        return organization

    def get_next_url_to_paginate(self, response):
        return response.links.get("next", {}).get("url")

    def get_paginated_results(self, response):
        return response.json()

    def get_webhook_data(self, project, integration):
        """Get webhook JSON data to post to the API."""
        return json.dumps(
            {
                "name": "web",
                "active": True,
                "config": {
                    "url": self.get_webhook_url(project, integration),
                    "secret": integration.secret,
                    "content_type": "json",
                },
                "events": ["push", "pull_request", "create", "delete"],
            }
        )

    def get_provider_data(self, project, integration):
        """
        Gets provider data from GitHub Webhooks API.

        :param project: project
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: Dictionary containing provider data from the API or None
        :rtype: dict
        """

        if integration.provider_data:
            return integration.provider_data

        owner, repo = build_utils.get_github_username_repo(url=project.repo)
        url = f"{self.base_api_url}/repos/{owner}/{repo}/hooks"
        structlog.contextvars.bind_contextvars(
            url=url,
            project_slug=project.slug,
            integration_id=integration.pk,
        )

        rtd_webhook_url = self.get_webhook_url(project, integration)

        try:
            resp = self.session.get(url)
            if resp.status_code == 200:
                recv_data = resp.json()

                for webhook_data in recv_data:
                    if webhook_data["config"]["url"] == rtd_webhook_url:
                        integration.provider_data = webhook_data
                        integration.save()

                        log.info(
                            "GitHub integration updated with provider data for project.",
                        )
                        break
            else:
                log.warning(
                    "GitHub project does not exist or user does not have permissions.",
                    https_status_code=resp.status_code,
                )

        except Exception:
            log.exception("GitHub webhook Listing failed for project.")

        return integration.provider_data

    def setup_webhook(self, project, integration=None) -> bool:
        """
        Set up GitHub project webhook for project.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: boolean based on webhook set up success, and requests Response object
        """
        owner, repo = build_utils.get_github_username_repo(url=project.repo)

        if not integration:
            integration, _ = Integration.objects.get_or_create(
                project=project,
                integration_type=Integration.GITHUB_WEBHOOK,
            )

        data = self.get_webhook_data(project, integration)
        url = f"{self.base_api_url}/repos/{owner}/{repo}/hooks"
        structlog.contextvars.bind_contextvars(
            url=url,
            project_slug=project.slug,
            integration_id=integration.pk,
        )
        resp = None
        try:
            resp = self.session.post(
                url,
                data=data,
                headers={"content-type": "application/json"},
            )
            structlog.contextvars.bind_contextvars(http_status_code=resp.status_code)

            # GitHub will return 200 if already synced
            if resp.status_code in [200, 201]:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.debug("GitHub webhook creation successful for project.")
                return True

            if resp.status_code in [401, 403, 404]:
                log.warning("GitHub project does not exist or user does not have permissions.")
            else:
                # Unknown response from GitHub
                try:
                    debug_data = resp.json()
                except ValueError:
                    debug_data = resp.content
                log.warning(
                    "GitHub webhook creation failed for project. Unknown response from GitHub.",
                    debug_data=debug_data,
                )

        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            log.exception("GitHub webhook creation failed for project.")

        return False

    def update_webhook(self, project, integration) -> bool:
        """
        Update webhook integration.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Webhook integration to update
        :type integration: Integration
        :returns: boolean based on webhook update success, and requests Response object
        """
        data = self.get_webhook_data(project, integration)
        resp = None

        provider_data = self.get_provider_data(project, integration)
        structlog.contextvars.bind_contextvars(
            project_slug=project.slug,
            integration_id=integration.pk,
        )

        # Handle the case where we don't have a proper provider_data set
        # This happens with a user-managed webhook previously
        if not provider_data:
            return self.setup_webhook(project, integration)

        try:
            url = provider_data.get("url")
            resp = self.session.patch(
                url,
                data=data,
                headers={"content-type": "application/json"},
            )
            structlog.contextvars.bind_contextvars(
                http_status_code=resp.status_code,
                url=url,
            )

            # GitHub will return 200 if already synced
            if resp.status_code in [200, 201]:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info("GitHub webhook update successful for project.")
                return True

            # GitHub returns 404 when the webhook doesn't exist. In this case,
            # we call ``setup_webhook`` to re-configure it from scratch
            if resp.status_code == 404:
                return self.setup_webhook(project, integration)

            # Unknown response from GitHub
            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.warning(
                "GitHub webhook update failed. Unknown response from GitHub",
                debug_data=debug_data,
            )

        # Catch exceptions with request or deserializing JSON
        except (AttributeError, RequestException, ValueError):
            log.exception("GitHub webhook update failed for project.")

        return False

    def remove_webhook(self, project):
        """
        Remove GitHub webhook for the repository associated with the project.

        We delete all webhooks that match the URL of the webhook we set up.
        The URLs can be in several formats, so we check for all of them:

        - https://app.readthedocs.org/api/v2/webhook/github/<project_slug>/<id>
        - https://app.readthedocs.org/api/v2/webhook/<project_slug>/<id>
        - https://readthedocs.org/api/v2/webhook/github/<project_slug>/<id>
        - https://readthedocs.org/api/v2/webhook/<project_slug>/<id>

        If a webhook fails to be removed, we log the error and cancel the operation,
        as if we weren't able to delete one webhook, we won't be able to delete the others either.

        If we didn't find any webhook to delete, we return True.
        """
        owner, repo = build_utils.get_github_username_repo(url=project.repo)

        try:
            resp = self.session.get(f"{self.base_api_url}/repos/{owner}/{repo}/hooks")
            resp.raise_for_status()
            data = resp.json()
        except HTTPError:
            log.info("Failed to get GitHub webhooks for project.")
            return False

        hook_targets = [
            f"{settings.PUBLIC_API_URL}/api/v2/webhook/{project.slug}/",
            f"{settings.PUBLIC_API_URL}/api/v2/webhook/github/{project.slug}/",
        ]
        hook_targets.append(hook_targets[0].replace("app.", "", 1))
        hook_targets.append(hook_targets[1].replace("app.", "", 1))

        for hook in data:
            hook_url = hook["config"]["url"]
            for hook_target in hook_targets:
                if hook_url.startswith(hook_target):
                    try:
                        self.session.delete(
                            f"{self.base_api_url}/repos/{owner}/{repo}/hooks/{hook['id']}"
                        ).raise_for_status()
                    except HTTPError:
                        log.info("Failed to remove GitHub webhook for project.")
                        return False
        return True

    def remove_ssh_key(self, project) -> bool:
        """
        Remove the SSH key from the GitHub repository associated with the project.

        This is overridden in .com, as we don't make use of the SSH keys in .org.
        """
        return True

    def send_build_status(self, *, build, commit, status):
        """
        Create GitHub commit status for project.

        :param build: Build to set up commit status for
        :type build: Build
        :param status: build state failure, pending, or success.
        :type status: str
        :param commit: commit sha of the pull request
        :type commit: str
        :returns: boolean based on commit status creation was successful or not.
        :rtype: Bool
        """
        project = build.project
        owner, repo = build_utils.get_github_username_repo(url=project.repo)

        # select the correct status and description.
        github_build_status = SELECT_BUILD_STATUS[status]["github"]
        description = SELECT_BUILD_STATUS[status]["description"]
        statuses_url = f"{self.base_api_url}/repos/{owner}/{repo}/statuses/{commit}"

        if status == BUILD_STATUS_SUCCESS:
            # Link to the documentation for this version
            target_url = build.version.get_absolute_url()
        else:
            # Link to the build detail's page
            target_url = build.get_full_url()

        context = f"{settings.RTD_BUILD_STATUS_API_NAME}:{project.slug}"

        data = {
            "state": github_build_status,
            "target_url": target_url,
            "description": description,
            "context": context,
        }

        structlog.contextvars.bind_contextvars(
            project_slug=project.slug,
            commit_status=github_build_status,
            user_username=self.user.username,
            statuses_url=statuses_url,
            target_url=target_url,
            status=status,
        )
        resp = None
        try:
            resp = self.session.post(
                statuses_url,
                data=json.dumps(data),
                headers={"content-type": "application/json"},
            )
            structlog.contextvars.bind_contextvars(http_status_code=resp.status_code)
            if resp.status_code == 201:
                log.debug("GitHub commit status created for project.")
                return True

            if resp.status_code in [401, 403, 404]:
                log.info("GitHub project does not exist or user does not have permissions.")
                return False

            if resp.status_code == 422 and "No commit found for SHA" in resp.json()["message"]:
                # This happens when the user force-push a branch or similar
                # that changes the Git history and SHA does not exist anymore.
                #
                # We return ``True`` here because otherwise our logic will try
                # with different users. However, all of them will fail since
                # it's not a permission issue.
                return True

            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.warning(
                "GitHub commit status creation failed. Unknown GitHub response.",
                debug_data=debug_data,
            )

        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            log.exception("GitHub commit status creation failed for project.")
        except InvalidGrantError:
            log.info("Invalid GitHub grant for user.", exc_info=True)
        except TokenExpiredError:
            log.info("GitHub token expired for user.", exc_info=True)

        return False
