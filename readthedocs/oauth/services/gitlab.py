"""OAuth utility functions."""

import json
import re
from urllib.parse import quote_plus
from urllib.parse import urlparse

import structlog
from allauth.socialaccount.providers.gitlab.provider import GitLabProvider
from django.conf import settings
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from requests.exceptions import RequestException

from readthedocs.builds import utils as build_utils
from readthedocs.builds.constants import BUILD_STATUS_SUCCESS
from readthedocs.builds.constants import SELECT_BUILD_STATUS
from readthedocs.integrations.models import Integration

from ..constants import GITLAB
from ..models import RemoteOrganization
from ..models import RemoteRepository
from .base import SyncServiceError
from .base import UserService


log = structlog.get_logger(__name__)


class GitLabService(UserService):
    """
    Provider service for GitLab.

    See:
     - https://docs.gitlab.com/ce/integration/oauth_provider.html
     - https://docs.gitlab.com/ce/api/oauth2.html
    """

    allauth_provider = GitLabProvider
    base_api_url = "https://gitlab.com"
    supports_build_status = True
    # Just use the network location to determine if it's a GitLab project
    # because private repos have another base url, eg. git@gitlab.example.com
    url_pattern = re.compile(
        re.escape(urlparse(base_api_url).netloc),
    )

    PERMISSION_NO_ACCESS = 0
    PERMISSION_MAINTAINER = 40
    PERMISSION_OWNER = 50

    vcs_provider_slug = GITLAB

    def _get_repo_id(self, project):
        """
        Get the ID or URL-encoded path of the project.

        See https://docs.gitlab.com/ce/api/README.html#namespaced-path-encoding.
        """
        if project.remote_repository:
            repo_id = project.remote_repository.remote_id
        else:
            # Handle "Manual Import" when there is no RemoteRepository
            # associated with the project. It only works with gitlab.com at the
            # moment (doesn't support custom gitlab installations)
            username, repo = build_utils.get_gitlab_username_repo(project.repo)
            if (username, repo) == (None, None):
                return None

            repo_id = quote_plus(f"{username}/{repo}")
        return repo_id

    def get_next_url_to_paginate(self, response):
        return response.links.get("next", {}).get("url")

    def get_paginated_results(self, response):
        return response.json()

    def sync_repositories(self):
        """
        Sync repositories that the user has access to.

        See https://docs.gitlab.com/api/projects/#list-a-users-projects.
        """
        remote_ids = []
        try:
            repos = self.paginate(
                f"{self.base_api_url}/api/v4/projects",
                membership=True,
                per_page=100,
                archived=False,
                order_by="path",
                sort="asc",
            )

            for repo in repos:
                remote_repository = self.create_repository(repo)
                if remote_repository:
                    remote_ids.append(remote_repository.remote_id)
        except (TypeError, ValueError):
            log.warning("Error syncing GitLab repositories")
            raise SyncServiceError(
                SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                    provider=self.vcs_provider_slug
                )
            )

        return remote_ids

    def sync_organizations(self):
        """
        Sync GitLab groups (organizations).

        This method only creates the relationships between the
        organizations and the user, as all the repositories
        are already created in the sync_repositories method.
        """
        organization_remote_ids = []

        try:
            orgs = self.paginate(
                f"{self.base_api_url}/api/v4/groups",
                per_page=100,
                all_available=False,
                order_by="path",
                sort="asc",
            )
            for org in orgs:
                remote_organization = self.create_organization(org)
                remote_organization.get_remote_organization_relation(self.user, self.account)
                organization_remote_ids.append(remote_organization.remote_id)
        except (TypeError, ValueError):
            log.warning("Error syncing GitLab organizations")
            raise SyncServiceError(
                SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                    provider=self.vcs_provider_slug
                )
            )

        return organization_remote_ids, []

    def _has_access_to_repository(self, fields):
        """Check if the user has access to the repository, and if they are an admin."""
        permissions = fields.get("permissions", {})
        project_access = permissions.get("project_access") or {}
        project_access_level = project_access.get("access_level", self.PERMISSION_NO_ACCESS)
        group_access = permissions.get("group_access") or {}
        group_access_level = group_access.get("access_level", self.PERMISSION_NO_ACCESS)
        has_access = (
            group_access_level != self.PERMISSION_NO_ACCESS
            or project_access_level != self.PERMISSION_NO_ACCESS
        )
        project_admin = project_access_level in (self.PERMISSION_MAINTAINER, self.PERMISSION_OWNER)
        group_admin = group_access_level in (self.PERMISSION_MAINTAINER, self.PERMISSION_OWNER)
        return has_access, project_admin or group_admin

    def update_repository(self, remote_repository: RemoteRepository):
        resp = self.session.get(
            f"{self.base_api_url}/api/v4/projects/{remote_repository.remote_id}"
        )

        if resp.status_code in [403, 404]:
            log.info(
                "User no longer has access to the repository, removing remote relationship.",
                remote_repository_id=remote_repository.remote_id,
            )
            remote_repository.get_remote_repository_relation(self.user, self.account).delete()
            return

        if resp.status_code != 200:
            log.warning(
                "Error fetching repository from GitLab",
                remote_repository_id=remote_repository.remote_id,
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
        Update or create a repository from GitLab API response.

        ``admin`` field is computed using the ``permissions`` fields from the
        repository response. The permission from GitLab is given by an integer:
          * 0: No access
          * (... others ...)
          * 40: Maintainer
          * 50: Owner

        https://docs.gitlab.com/ee/api/access_requests.html
        https://gitlab.com/help/user/permissions

        :param fields: dictionary of response data from API
        :param privacy: privacy level to support
        :rtype: RemoteRepository
        """
        privacy = privacy or settings.DEFAULT_PRIVACY_LEVEL
        repo_is_public = fields["visibility"] == "public"
        if privacy == "private" or (repo_is_public and privacy == "public"):
            repo, _ = RemoteRepository.objects.get_or_create(
                remote_id=fields["id"], vcs_provider=self.vcs_provider_slug
            )
            self._update_repository_from_fields(repo, fields)

            remote_repository_relation = repo.get_remote_repository_relation(
                self.user, self.account
            )
            _, is_admin = self._has_access_to_repository(fields)
            remote_repository_relation.admin = is_admin
            remote_repository_relation.save()

            return repo

        log.info(
            "Not importing repository because mismatched type.",
            repository=fields["path_with_namespace"],
            visibility=fields["visibility"],
        )

    def _update_repository_from_fields(self, repo, fields):
        # If the namespace is a group, we can use it as the organization
        if fields.get("namespace", {}).get("kind") == "group":
            organization = self.create_organization(fields["namespace"])
            repo.organization = organization
        else:
            repo.organization = None

        repo.name = fields["name"]
        repo.full_name = fields["path_with_namespace"]
        repo.description = fields["description"]
        repo.ssh_url = fields["ssh_url_to_repo"]
        repo.html_url = fields["web_url"]
        repo.vcs = "git"
        repo.private = fields["visibility"] == "private"
        repo.default_branch = fields.get("default_branch")

        owner = fields.get("owner") or {}
        repo.avatar_url = self._make_absolute_url(
            fields.get("avatar_url") or owner.get("avatar_url")
        )

        if not repo.avatar_url:
            repo.avatar_url = self.default_user_avatar_url

        if repo.private:
            repo.clone_url = repo.ssh_url
        else:
            repo.clone_url = fields["http_url_to_repo"]

        repo.save()

    def _make_absolute_url(self, url):
        """
        Make sure the URL is absolute to gitlab.com.

        If the URL is relative, prepend the base API URL.
        """
        if url and not url.startswith("http"):
            return f"https://gitlab.com{url}"
        return url

    def create_organization(self, fields):
        """
        Update or create remote organization from GitLab API response.

        :param fields: dictionary response of data from API
        :rtype: RemoteOrganization

        .. note::

           This method caches organizations by their remote ID to avoid
           unnecessary database queries, specially when creating
           multiple repositories that belong to the same organization.
        """
        organization_id = fields["id"]
        if organization_id in self._organizations_cache:
            return self._organizations_cache[organization_id]

        organization, _ = RemoteOrganization.objects.get_or_create(
            remote_id=organization_id,
            vcs_provider=self.vcs_provider_slug,
        )

        organization.name = fields.get("name")
        organization.slug = fields.get("full_path")
        organization.url = fields.get("web_url")
        organization.avatar_url = self._make_absolute_url(fields.get("avatar_url"))

        if not organization.avatar_url:
            organization.avatar_url = self.default_user_avatar_url

        organization.save()

        self._organizations_cache[organization_id] = organization
        return organization

    def get_webhook_data(self, repo_id, project, integration):
        """
        Get webhook JSON data to post to the API.

        See: http://doc.gitlab.com/ce/api/projects.html#add-project-hook
        """
        return json.dumps(
            {
                "id": repo_id,
                "push_events": True,
                "tag_push_events": True,
                "url": self.get_webhook_url(project, integration),
                "token": integration.secret,
                # Optional
                "issues_events": False,
                "merge_requests_events": True,
                "note_events": False,
                "job_events": False,
                "pipeline_events": False,
                "wiki_events": False,
            }
        )

    def get_provider_data(self, project, integration):
        """
        Gets provider data from GitLab Webhooks API.

        :param project: project
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: Dictionary containing provider data from the API or None
        :rtype: dict
        """

        if integration.provider_data:
            return integration.provider_data

        repo_id = self._get_repo_id(project)

        if repo_id is None:
            return None

        structlog.contextvars.bind_contextvars(
            project_slug=project.slug,
            integration_id=integration.pk,
        )

        rtd_webhook_url = self.get_webhook_url(project, integration)

        try:
            resp = self.session.get(
                "{url}/api/v4/projects/{repo_id}/hooks".format(
                    url=self.base_api_url,
                    repo_id=repo_id,
                ),
            )

            if resp.status_code == 200:
                recv_data = resp.json()

                for webhook_data in recv_data:
                    if webhook_data["url"] == rtd_webhook_url:
                        integration.provider_data = webhook_data
                        integration.save()

                        log.info(
                            "GitLab integration updated with provider data for project.",
                        )
                        break
            else:
                log.info("GitLab project does not exist or user does not have permissions.")

        except Exception:
            log.exception("GitLab webhook Listing failed for project.")

        return integration.provider_data

    def setup_webhook(self, project, integration=None) -> bool:
        """
        Set up GitLab project webhook for project.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Integration for a project
        :type integration: Integration
        :returns: boolean based on webhook set up success
        :rtype: bool
        """
        resp = None

        if not integration:
            integration, _ = Integration.objects.get_or_create(
                project=project,
                integration_type=Integration.GITLAB_WEBHOOK,
            )

        repo_id = self._get_repo_id(project)
        url = f"{self.base_api_url}/api/v4/projects/{repo_id}/hooks"

        if repo_id is None:
            return False

        structlog.contextvars.bind_contextvars(
            project_slug=project.slug,
            integration_id=integration.pk,
            url=url,
        )
        data = self.get_webhook_data(repo_id, project, integration)
        try:
            resp = self.session.post(
                url,
                data=data,
                headers={"content-type": "application/json"},
            )
            structlog.contextvars.bind_contextvars(http_status_code=resp.status_code)

            if resp.status_code == 201:
                integration.provider_data = resp.json()
                integration.save()
                log.debug("GitLab webhook creation successful for project.")
                return True

            if resp.status_code in [401, 403, 404]:
                log.info("Gitlab project does not exist or user does not have permissions.")
            else:
                log.warning("GitLab webhook creation failed. Unknown response from GitLab.")

        except Exception:
            log.exception("GitLab webhook creation failed.")

        return False

    def update_webhook(self, project, integration) -> bool:
        """
        Update webhook integration.

        :param project: project to set up webhook for
        :type project: Project

        :param integration: Webhook integration to update
        :type integration: Integration

        :returns: boolean based on webhook update success, and requests Response
                  object
        """
        provider_data = self.get_provider_data(project, integration)

        # Handle the case where we don't have a proper provider_data set
        # This happens with a user-managed webhook previously
        if not provider_data:
            return self.setup_webhook(project, integration)

        resp = None
        repo_id = self._get_repo_id(project)

        if repo_id is None:
            return False

        data = self.get_webhook_data(repo_id, project, integration)

        structlog.contextvars.bind_contextvars(
            project_slug=project.slug,
            integration_id=integration.pk,
        )
        try:
            hook_id = provider_data.get("id")
            resp = self.session.put(
                "{url}/api/v4/projects/{repo_id}/hooks/{hook_id}".format(
                    url=self.base_api_url,
                    repo_id=repo_id,
                    hook_id=hook_id,
                ),
                data=data,
                headers={"content-type": "application/json"},
            )

            if resp.status_code == 200:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info("GitLab webhook update successful for project.")
                return True

            # GitLab returns 404 when the webhook doesn't exist. In this case,
            # we call ``setup_webhook`` to re-configure it from scratch
            if resp.status_code == 404:
                return self.setup_webhook(project, integration)

        except Exception:
            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            except Exception:
                debug_data = None
            log.exception(
                "GitLab webhook update failed.",
                debug_data=debug_data,
            )

        return False

    def send_build_status(self, *, build, commit, status):
        """
        Create GitLab commit status for project.

        :param build: Build to set up commit status for
        :type build: Build
        :param status: build status failure, pending, or success.
        :type status: str
        :param commit: commit sha of the pull request
        :type commit: str
        :returns: boolean based on commit status creation was successful or not.
        :rtype: Bool
        """
        resp = None
        project = build.project

        repo_id = self._get_repo_id(project)

        if repo_id is None:
            return (False, resp)

        # select the correct status and description.
        gitlab_build_state = SELECT_BUILD_STATUS[status]["gitlab"]
        description = SELECT_BUILD_STATUS[status]["description"]

        if status == BUILD_STATUS_SUCCESS:
            # Link to the documentation for this version
            target_url = build.version.get_absolute_url()
        else:
            # Link to the build detail's page
            target_url = build.get_full_url()

        context = f"{settings.RTD_BUILD_STATUS_API_NAME}:{project.slug}"

        data = {
            "state": gitlab_build_state,
            "target_url": target_url,
            "description": description,
            "context": context,
        }
        url = f"{self.base_api_url}/api/v4/projects/{repo_id}/statuses/{commit}"

        structlog.contextvars.bind_contextvars(
            project_slug=project.slug,
            commit_status=gitlab_build_state,
            user_username=self.user.username,
            url=url,
        )
        try:
            resp = self.session.post(
                url,
                data=json.dumps(data),
                headers={"content-type": "application/json"},
            )

            structlog.contextvars.bind_contextvars(http_status_code=resp.status_code)
            if resp.status_code == 201:
                log.debug("GitLab commit status created for project.")
                return True

            if resp.status_code in [401, 403, 404]:
                log.info("GitLab project does not exist or user does not have permissions.")
                return False

            return False

        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            # Response data should always be JSON, still try to log if not
            # though
            if resp is not None:
                try:
                    debug_data = resp.json()
                except ValueError:
                    debug_data = resp.content
            else:
                debug_data = resp

            log.exception(
                "GitLab commit status creation failed.",
                debug_data=debug_data,
            )
        except InvalidGrantError:
            log.info("Invalid GitLab grant for user.", exc_info=True)
        except TokenExpiredError:
            log.info("GitLab token expired for user.", exc_info=True)

        return False
