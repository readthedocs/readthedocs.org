"""OAuth utility functions."""

import json
import re

import structlog
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from django.conf import settings
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError, TokenExpiredError
from requests.exceptions import RequestException

from readthedocs.builds import utils as build_utils
from readthedocs.builds.constants import BUILD_STATUS_SUCCESS, SELECT_BUILD_STATUS
from readthedocs.integrations.models import Integration

from ..constants import GITHUB
from ..models import RemoteOrganization, RemoteRepository
from .base import Service, SyncServiceError

log = structlog.get_logger(__name__)


class GitHubService(Service):

    """Provider service for GitHub."""

    adapter = GitHubOAuth2Adapter
    # TODO replace this with a less naive check
    url_pattern = re.compile(r"github\.com")
    vcs_provider_slug = GITHUB

    def sync_repositories(self):
        """Sync repositories from GitHub API."""
        remote_repositories = []

        try:
            repos = self.paginate("https://api.github.com/user/repos", per_page=100)
            for repo in repos:
                remote_repository = self.create_repository(repo)
                remote_repositories.append(remote_repository)
        except (TypeError, ValueError):
            log.warning("Error syncing GitHub repositories")
            raise SyncServiceError(
                SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                    provider=self.vcs_provider_slug
                )
            )
        return remote_repositories

    def sync_organizations(self):
        """Sync organizations from GitHub API."""
        remote_organizations = []
        remote_repositories = []

        try:
            orgs = self.paginate("https://api.github.com/user/orgs", per_page=100)
            for org in orgs:
                org_details = self.get_session().get(org["url"]).json()
                remote_organization = self.create_organization(
                    org_details,
                    create_user_relationship=True,
                )
                remote_organizations.append(remote_organization)

                org_url = org["url"]
                org_repos = self.paginate(
                    f"{org_url}/repos",
                    per_page=100,
                )
                for repo in org_repos:
                    remote_repository = self.create_repository(repo)
                    remote_repositories.append(remote_repository)

        except (TypeError, ValueError):
            log.warning("Error syncing GitHub organizations")
            raise SyncServiceError(
                SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                    provider=self.vcs_provider_slug
                )
            )

        return remote_organizations, remote_repositories

    def create_repository(self, fields, privacy=None):
        """
        Update or create a repository from GitHub API response.

        :param fields: dictionary of response data from API
        :param privacy: privacy level to support
        :param organization: remote organization to associate with
        :type organization: RemoteOrganization
        :rtype: RemoteRepository
        """
        privacy = privacy or settings.DEFAULT_PRIVACY_LEVEL
        if any(
            [
                (privacy == "private"),
                (fields["private"] is False and privacy == "public"),
            ]
        ):
            repo, created = RemoteRepository.objects.get_or_create(
                remote_id=str(fields["id"]),
                vcs_provider=self.vcs_provider_slug,
            )

            # TODO: For debugging: https://github.com/readthedocs/readthedocs.org/pull/9449.
            if created:
                _old_remote_repository = RemoteRepository.objects.filter(
                    full_name=fields["full_name"], vcs_provider=self.vcs_provider_slug
                ).first()
                if _old_remote_repository:
                    log.warning(
                        "GitHub repository created with different remote_id but exact full_name.",
                        fields=fields,
                        old_remote_repository=_old_remote_repository.__dict__,
                        imported=_old_remote_repository.projects.exists(),
                    )

            owner_type = fields["owner"]["type"]
            organization = None
            if owner_type == "Organization":
                # We aren't creating a remote relationship between the current user
                # and the organization, since the user can have access to the repository,
                # but not to the organization.
                organization = self.create_organization(
                    fields=fields["owner"],
                    create_user_relationship=False,
                )

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

            remote_repository_relation = repo.get_remote_repository_relation(
                self.user, self.account
            )
            remote_repository_relation.admin = fields.get("permissions", {}).get(
                "admin", False
            )
            remote_repository_relation.save()

            return repo

        log.debug(
            "Not importing repository because mismatched type.",
            repository=fields["name"],
        )

    def create_organization(self, fields, create_user_relationship=False):
        """
        Update or create remote organization from GitHub API response.

        :param fields: dictionary response of data from API
        :param bool create_relationship: Whether to create a remote relationship between the
         organization and the current user. If `False`, only the `RemoteOrganization` object
         will be created/updated.
        :rtype: RemoteOrganization
        """
        organization, _ = RemoteOrganization.objects.get_or_create(
            remote_id=str(fields["id"]),
            vcs_provider=self.vcs_provider_slug,
        )
        if create_user_relationship:
            organization.get_remote_organization_relation(self.user, self.account)

        organization.url = fields.get("html_url")
        # fields['login'] contains GitHub Organization slug
        organization.slug = fields.get("login")
        organization.name = fields.get("name")
        organization.email = fields.get("email")
        organization.avatar_url = fields.get("avatar_url")

        if not organization.avatar_url:
            organization.avatar_url = self.default_org_avatar_url

        organization.save()

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

        session = self.get_session()
        owner, repo = build_utils.get_github_username_repo(url=project.repo)
        url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
        log.bind(
            url=url,
            project_slug=project.slug,
            integration_id=integration.pk,
        )

        rtd_webhook_url = self.get_webhook_url(project, integration)

        try:
            resp = session.get(url)
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

    def setup_webhook(self, project, integration=None):
        """
        Set up GitHub project webhook for project.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: boolean based on webhook set up success, and requests Response object
        :rtype: (Bool, Response)
        """
        session = self.get_session()
        owner, repo = build_utils.get_github_username_repo(url=project.repo)

        if not integration:
            integration, _ = Integration.objects.get_or_create(
                project=project,
                integration_type=Integration.GITHUB_WEBHOOK,
            )

        data = self.get_webhook_data(project, integration)
        url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
        log.bind(
            url=url,
            project_slug=project.slug,
            integration_id=integration.pk,
        )
        resp = None
        try:
            resp = session.post(
                url,
                data=data,
                headers={"content-type": "application/json"},
            )
            log.bind(http_status_code=resp.status_code)

            # GitHub will return 200 if already synced
            if resp.status_code in [200, 201]:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.debug("GitHub webhook creation successful for project.")
                return (True, resp)

            if resp.status_code in [401, 403, 404]:
                log.warning(
                    "GitHub project does not exist or user does not have permissions."
                )
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

        return (False, resp)

    def update_webhook(self, project, integration):
        """
        Update webhook integration.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Webhook integration to update
        :type integration: Integration
        :returns: boolean based on webhook update success, and requests Response object
        :rtype: (Bool, Response)
        """
        session = self.get_session()
        data = self.get_webhook_data(project, integration)
        resp = None

        provider_data = self.get_provider_data(project, integration)
        log.bind(
            project_slug=project.slug,
            integration_id=integration.pk,
        )

        # Handle the case where we don't have a proper provider_data set
        # This happens with a user-managed webhook previously
        if not provider_data:
            return self.setup_webhook(project, integration)

        try:
            url = provider_data.get("url")
            resp = session.patch(
                url,
                data=data,
                headers={"content-type": "application/json"},
            )
            log.bind(
                http_status_code=resp.status_code,
                url=url,
            )

            # GitHub will return 200 if already synced
            if resp.status_code in [200, 201]:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info("GitHub webhook update successful for project.")
                return (True, resp)

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

        return (False, resp)

    def send_build_status(self, build, commit, status):
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
        session = self.get_session()
        project = build.project
        owner, repo = build_utils.get_github_username_repo(url=project.repo)

        # select the correct status and description.
        github_build_status = SELECT_BUILD_STATUS[status]["github"]
        description = SELECT_BUILD_STATUS[status]["description"]
        statuses_url = f"https://api.github.com/repos/{owner}/{repo}/statuses/{commit}"

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

        log.bind(
            project_slug=project.slug,
            commit_status=github_build_status,
            user_username=self.user.username,
            statuses_url=statuses_url,
            target_url=target_url,
            status=status,
        )
        resp = None
        try:
            resp = session.post(
                statuses_url,
                data=json.dumps(data),
                headers={"content-type": "application/json"},
            )
            log.bind(http_status_code=resp.status_code)
            if resp.status_code == 201:
                log.debug("GitHub commit status created for project.")
                return True

            if resp.status_code in [401, 403, 404]:
                log.info(
                    "GitHub project does not exist or user does not have permissions."
                )
                return False

            if (
                resp.status_code == 422
                and "No commit found for SHA" in resp.json()["message"]
            ):
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
