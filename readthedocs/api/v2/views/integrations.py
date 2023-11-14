"""Endpoints integrating with Github, Bitbucket, and other webhooks."""

import hashlib
import hmac
import json
import re
from functools import namedtuple
from textwrap import dedent

import structlog
from django.shortcuts import get_object_or_404
from django.utils.crypto import constant_time_compare
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from readthedocs.builds.constants import LATEST
from readthedocs.core.signals import webhook_bitbucket, webhook_github, webhook_gitlab
from readthedocs.core.views.hooks import (
    build_branches,
    build_external_version,
    close_external_version,
    get_or_create_external_version,
    trigger_sync_versions,
)
from readthedocs.integrations.models import HttpExchange, Integration
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)

GITHUB_EVENT_HEADER = "X-GitHub-Event"
GITHUB_SIGNATURE_HEADER = "X-Hub-Signature-256"
GITHUB_PING = "ping"
GITHUB_PUSH = "push"
GITHUB_PULL_REQUEST = "pull_request"
GITHUB_PULL_REQUEST_OPENED = "opened"
GITHUB_PULL_REQUEST_CLOSED = "closed"
GITHUB_PULL_REQUEST_REOPENED = "reopened"
GITHUB_PULL_REQUEST_SYNC = "synchronize"
GITHUB_CREATE = "create"
GITHUB_DELETE = "delete"
GITLAB_MERGE_REQUEST = "merge_request"
GITLAB_MERGE_REQUEST_CLOSE = "close"
GITLAB_MERGE_REQUEST_MERGE = "merge"
GITLAB_MERGE_REQUEST_OPEN = "open"
GITLAB_MERGE_REQUEST_REOPEN = "reopen"
GITLAB_MERGE_REQUEST_UPDATE = "update"
GITLAB_TOKEN_HEADER = "X-GitLab-Token"
GITLAB_PUSH = "push"
GITLAB_NULL_HASH = "0" * 40
GITLAB_TAG_PUSH = "tag_push"
BITBUCKET_EVENT_HEADER = "X-Event-Key"
BITBUCKET_SIGNATURE_HEADER = "X-Hub-Signature"
BITBUCKET_PUSH = "repo:push"


ExternalVersionData = namedtuple(
    "ExternalVersionData",
    ["id", "source_branch", "base_branch", "commit"],
)


class WebhookMixin:

    """Base class for Webhook mixins."""

    permission_classes = (permissions.AllowAny,)
    renderer_classes = (JSONRenderer,)
    integration = None
    integration_type = None
    invalid_payload_msg = 'Payload not valid'
    missing_secret_for_pr_events_msg = dedent(
        """
        The webhook doesn't have a secret configured.
        For security reasons, webhooks without a secret can't process pull/merge request events.
        You can read more information about this in our blog post: https://blog.readthedocs.com/security-update-on-incoming-webhooks/.
        """
    ).strip()

    def post(self, request, project_slug):
        """Set up webhook post view with request and project objects."""
        self.request = request

        log.bind(
            project_slug=project_slug,
            integration_type=self.integration_type,
        )

        # WARNING: this is a hack to allow us access to `request.body` later.
        # Due to a limitation of DRF, we can't access `request.body`
        # after accessing `request.data`.
        # By accessing `request.body` we are able to access `request.body` and
        # `request.data` later without any problem (mostly black magic).
        # See #4940 for more background.
        self.request.body  # noqa
        self.project = None
        self.data = self.get_data()
        try:
            self.project = self.get_project(slug=project_slug)
            if not Project.objects.is_active(self.project):
                resp = {'detail': 'This project is currently disabled'}
                return Response(resp, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Project.DoesNotExist as exc:
            raise NotFound("Project not found") from exc
        if not self.is_payload_valid():
            log.warning('Invalid payload for project and integration.')
            return Response(
                {'detail': self.invalid_payload_msg},
                status=HTTP_400_BAD_REQUEST,
            )
        resp = self.handle_webhook()
        if resp is None:
            log.info('Unhandled webhook event')
            resp = {'detail': 'Unhandled webhook event'}

        # The response can be a DRF Response with with the status code already set.
        # In that case, we just return it as is.
        if isinstance(resp, Response):
            return resp
        return Response(resp)

    def get_project(self, **kwargs):
        return Project.objects.get(**kwargs)

    def finalize_response(self, req, *args, **kwargs):
        """If the project was set on POST, store an HTTP exchange."""
        resp = super().finalize_response(req, *args, **kwargs)
        if hasattr(self, 'project') and self.project:
            HttpExchange.objects.from_exchange(
                req,
                resp,
                related_object=self.get_integration(),
                payload=self.data,
            )
        return resp

    def get_data(self):
        """
        Normalize posted data.

        This can be overridden to support multiples content types.
        """
        return self.request.data

    def handle_webhook(self):
        """Handle webhook payload."""
        raise NotImplementedError

    def get_external_version_data(self):
        """Get External Version data from payload."""
        raise NotImplementedError

    def is_payload_valid(self):
        """Validates the webhook's payload using the integration's secret."""
        return False

    @staticmethod
    def get_digest(secret, msg):
        """Get a HMAC digest of `msg` using `secret`."""
        digest = hmac.new(
            secret.encode(),
            msg=msg.encode(),
            digestmod=hashlib.sha256,
        )
        return digest.hexdigest()

    def get_integration(self):
        """
        Get or create an inbound webhook to track webhook requests.

        Most providers don't pass the webhook ID in either, so we default
        to just finding *any* integration from the provider. This is not ideal,
        but the :py:class:`WebhookView` view solves this by performing a lookup
        on the integration instead of guessing.
        """
        # `integration` can be passed in as an argument to `as_view`, as it is
        # in `WebhookView`
        if self.integration is not None:
            return self.integration
        self.integration = get_object_or_404(
            Integration,
            project=self.project,
            integration_type=self.integration_type,
        )
        return self.integration

    def get_response_push(self, project, branches):
        """
        Build branches on push events and return API response.

        Return a JSON response with the following::

            {
                "build_triggered": true,
                "project": "project_name",
                "versions": [...]
            }

        :param project: Project instance
        :type project: Project
        :param branches: List of branch/tag names to build
        :type branches: list(str)
        """
        to_build, not_building = build_branches(project, branches)
        if not_building:
            log.info(
                'Skipping project branches.',
                branches=branches,
            )
        triggered = bool(to_build)
        return {
            'build_triggered': triggered,
            'project': project.slug,
            'versions': list(to_build),
        }

    def sync_versions_response(self, project, sync=True):
        """
        Trigger a sync and returns a response indicating if the build was triggered or not.

        If `sync` is False, the sync isn't triggered and a response indicating so is returned.
        """
        version = None
        if sync:
            version = trigger_sync_versions(project)
        return {
            'build_triggered': False,
            'project': project.slug,
            'versions': [version] if version else [],
            'versions_synced': version is not None,
        }

    def get_external_version_response(self, project):
        """
        Trigger builds for External versions on pull/merge request events and return API response.

        Return a JSON response with the following::

            {
                "build_triggered": true,
                "project": "project_name",
                "versions": [verbose_name]
            }

        :param project: Project instance
        :type project: readthedocs.projects.models.Project
        """
        version_data = self.get_external_version_data()
        # create or get external version object using `verbose_name`.
        external_version = get_or_create_external_version(
            project=project,
            version_data=version_data,
        )
        # returns external version verbose_name (pull/merge request number)
        to_build = build_external_version(
            project=project,
            version=external_version,
        )

        return {
            "build_triggered": bool(to_build),
            "project": project.slug,
            "versions": [to_build] if to_build else [],
        }

    def get_closed_external_version_response(self, project):
        """
        Close the external version on merge/close events and return the API response.

        Return a JSON response with the following::

            {
                "closed": true,
                "project": "project_name",
                "versions": [verbose_name]
            }

        :param project: Project instance
        :type project: Project
        """
        version_data = self.get_external_version_data()
        version_closed = close_external_version(
            project=project,
            version_data=version_data,
        )
        return {
            "closed": bool(version_closed),
            "project": project.slug,
            "versions": [version_closed] if version_closed else [],
        }

    def update_default_branch(self, default_branch):
        """
        Update the `Version.identifer` for `latest` with the VCS's `default_branch`.

        The VCS's `default_branch` is the branch cloned when there is no specific branch specified
        (e.g. `git clone <URL>`).

        Some VCS providers (GitHub and GitLab) send the `default_branch` via incoming webhooks.
        We use that data to update our database and keep it in sync.

        This solves the problem about "changing the default branch in GitHub"
        and also importing repositories with a different `default_branch` than `main` manually:
        https://github.com/readthedocs/readthedocs.org/issues/9367

        In case the user already selected a `default-branch` from the "Advanced settings",
        it does not override it.

        This action can be performed only if the integration has a secret,
        requests from anonymous users are ignored.
        """
        if self.get_integration().secret and not self.project.default_branch:
            # Always check for the machine attribute, since latest can be user created.
            # RTD doesn't manage those.
            self.project.versions.filter(slug=LATEST, machine=True).update(
                identifier=default_branch
            )


class GitHubWebhookView(WebhookMixin, APIView):

    """
    Webhook consumer for GitHub.

    Accepts webhook events from GitHub, 'push' and 'pull_request' events trigger builds.
    Expects the webhook event type will be included in HTTP header ``X-GitHub-Event``,
    and we will have a JSON payload.

    Expects the following JSON::

        For push, create, delete Events:
            {
                "ref": "branch-name",
                ...
            }

        For pull_request Events:
            {
                "action": "opened",
                "number": 2,
                "pull_request": {
                    "head": {
                        "sha": "ec26de721c3235aad62de7213c562f8c821"
                    }
                }
            }

    See full payload here:

    - https://developer.github.com/v3/activity/events/types/#pushevent
    - https://developer.github.com/v3/activity/events/types/#createevent
    - https://developer.github.com/v3/activity/events/types/#deleteevent
    - https://developer.github.com/v3/activity/events/types/#pullrequestevent
    """

    integration_type = Integration.GITHUB_WEBHOOK
    invalid_payload_msg = 'Payload not valid, invalid or missing signature'

    def get_data(self):
        if self.request.content_type == 'application/x-www-form-urlencoded':
            try:
                return json.loads(self.request.data['payload'])
            except (ValueError, KeyError):
                pass
        return super().get_data()

    def get_external_version_data(self):
        """Get Commit Sha and pull request number from payload."""
        try:
            data = ExternalVersionData(
                id=str(self.data["number"]),
                commit=self.data["pull_request"]["head"]["sha"],
                source_branch=self.data["pull_request"]["head"]["ref"],
                base_branch=self.data["pull_request"]["base"]["ref"],
            )
            return data
        except KeyError as e:
            key = e.args[0]
            raise ParseError(f"Invalid payload. {key} is required.") from e

    def is_payload_valid(self):
        """
        GitHub use a HMAC hexdigest hash to sign the payload.

        It is sent in the request's header.

        See https://developer.github.com/webhooks/securing/.
        """
        signature = self.request.headers.get(GITHUB_SIGNATURE_HEADER)
        secret = self.get_integration().secret
        if not secret:
            log.debug('Skipping payload signature validation.')
            return True
        if not signature:
            return False
        msg = self.request.body.decode()
        digest = WebhookMixin.get_digest(secret, msg)
        result = hmac.compare_digest(
            b"sha256=" + digest.encode(),
            signature.encode(),
        )
        return result

    def handle_webhook(self):
        """
        Handle GitHub webhook events.

        It checks for all the events we support currently:

        - PUSH: Triggered on a push to a repository branch. Branch pushes and repository tag pushes
          also trigger webhook push events.

          .. note::

            ``created`` and ``deleted`` indicate if the push was a branch/tag created or deleted.
            This is required for old webhook created at Read the Docs that do not register the
            ``create`` and ``delete`` events.

            Newer webhooks created on Read the Docs, will trigger a PUSH+created=True **and** a
            CREATE event. We need to handle this in a specific way to not trigger the sync twice.

        - CREATE: Represents a created branch or tag.

        - DELETE: Represents a deleted branch or tag.

        - PULL_REQUEST: Triggered when a pull request is assigned, unassigned, labeled, unlabeled,
          opened, edited, closed, reopened, synchronize, ready_for_review, locked, unlocked or when
          a pull request review is requested or removed (``action`` will contain this data)

        See https://developer.github.com/v3/activity/events/types/

        """
        # Get event and trigger other webhook events
        action = self.data.get('action', None)
        created = self.data.get('created', False)
        deleted = self.data.get('deleted', False)
        event = self.request.headers.get(GITHUB_EVENT_HEADER, GITHUB_PUSH)
        log.bind(webhook_event=event)
        webhook_github.send(
            Project,
            project=self.project,
            data=self.data,
            event=event,
        )

        # Always update `latest` branch to point to the default branch in the repository
        # even if the event is not gonna be handled. This helps us to keep our db in sync.
        default_branch = self.data.get("repository", {}).get("default_branch", None)
        if default_branch:
            self.update_default_branch(default_branch)

        if event == GITHUB_PING:
            return {"detail": "Webhook configured correctly"}

        # Sync versions when a branch/tag was created/deleted
        if event in (GITHUB_CREATE, GITHUB_DELETE):
            log.debug('Triggered sync_versions.')
            return self.sync_versions_response(self.project)

        integration = self.get_integration()

        # Handle pull request events.
        if self.project.external_builds_enabled and event == GITHUB_PULL_REQUEST:
            # Requests from anonymous users are ignored.
            if not integration.secret:
                return Response(
                    {"detail": self.missing_secret_for_pr_events_msg},
                    status=HTTP_400_BAD_REQUEST,
                )

            if action in [
                GITHUB_PULL_REQUEST_OPENED,
                GITHUB_PULL_REQUEST_REOPENED,
                GITHUB_PULL_REQUEST_SYNC,
            ]:
                # Trigger a build when PR is opened/reopened/sync
                return self.get_external_version_response(self.project)

            if action == GITHUB_PULL_REQUEST_CLOSED:
                # Delete external version when PR is closed
                return self.get_closed_external_version_response(self.project)

        # Sync versions when push event is created/deleted action
        if all([
                event == GITHUB_PUSH,
                (created or deleted),
        ]):
            events = integration.provider_data.get('events', []) if integration.provider_data else []  # noqa
            if any([
                    GITHUB_CREATE in events,
                    GITHUB_DELETE in events,
            ]):
                # GitHub will send PUSH **and** CREATE/DELETE events on a creation/deletion in newer
                # webhooks. If we receive a PUSH event we need to check if the webhook doesn't
                # already have the CREATE/DELETE events. So we don't trigger the sync twice.
                return self.sync_versions_response(self.project, sync=False)

            log.debug(
                'Triggered sync_versions.',
                integration_events=events,
            )
            return self.sync_versions_response(self.project)

        # Trigger a build for all branches in the push
        if event == GITHUB_PUSH:
            try:
                branch = self._normalize_ref(self.data["ref"])
                return self.get_response_push(self.project, [branch])
            except KeyError as exc:
                raise ParseError('Parameter "ref" is required') from exc

        return None

    def _normalize_ref(self, ref):
        """Remove `ref/(heads|tags)/` from the reference to match a Version on the db."""
        pattern = re.compile(r'^refs/(heads|tags)/')
        return pattern.sub('', ref)


class GitLabWebhookView(WebhookMixin, APIView):

    """
    Webhook consumer for GitLab.

    Accepts webhook events from GitLab, 'push' and 'merge_request' events trigger builds.

    Expects the following JSON::

        {
            "before": "95790bf891e76fee5e1747ab589903a6a1f80f22",
            "after": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
            "object_kind": "push",
            "ref": "branch-name",
            ...
        }

    For merge_request events:

        {
            "object_kind": "merge_request",
            "object_attributes": {
                "iid": 2,
                "last_commit": {
                "id": "717abb9a6a0f3111dbd601ef6f58c70bdd165aef",
                },
                "action": "open"
                ...
            },
            ...
        }

    See full payload here:

    - https://docs.gitlab.com/ce/user/project/integrations/webhooks.html#push-events
    - https://docs.gitlab.com/ce/user/project/integrations/webhooks.html#tag-events
    - https://docs.gitlab.com/ce/user/project/integrations/webhooks.html#merge-request-events
    """

    integration_type = Integration.GITLAB_WEBHOOK
    invalid_payload_msg = 'Payload not valid, invalid or missing token'

    def is_payload_valid(self):
        """
        GitLab only sends back the token from the webhook.

        It is sent in the request's header.
        See https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#secret-token.
        """
        token = self.request.headers.get(GITLAB_TOKEN_HEADER, "")
        secret = self.get_integration().secret
        if not secret:
            log.debug('Skipping payload signature validation.')
            return True
        return constant_time_compare(secret, token)

    def get_external_version_data(self):
        """Get commit SHA and merge request number from payload."""
        try:
            data = ExternalVersionData(
                id=str(self.data["object_attributes"]["iid"]),
                commit=self.data["object_attributes"]["last_commit"]["id"],
                source_branch=self.data["object_attributes"]["source_branch"],
                base_branch=self.data["object_attributes"]["target_branch"],
            )
            return data
        except KeyError as e:
            key = e.args[0]
            raise ParseError(f"Invalid payload. {key} is required.") from e

    def handle_webhook(self):
        """
        Handle GitLab events for push and tag_push.

        GitLab doesn't have a separate event for creation/deletion,
        instead, it sets the before/after field to
        0000000000000000000000000000000000000000 ('0' * 40)
        """
        event = self.request.data.get('object_kind', GITLAB_PUSH)
        action = self.data.get('object_attributes', {}).get('action', None)
        log.bind(webhook_event=event)
        webhook_gitlab.send(
            Project,
            project=self.project,
            data=self.request.data,
            event=event,
        )

        integration = self.get_integration()

        # Always update `latest` branch to point to the default branch in the repository
        # even if the event is not gonna be handled. This helps us to keep our db in sync.
        default_branch = self.data.get("project", {}).get("default_branch", None)
        if default_branch:
            self.update_default_branch(default_branch)

        # Handle push events and trigger builds
        if event in (GITLAB_PUSH, GITLAB_TAG_PUSH):
            data = self.request.data
            before = data.get('before')
            after = data.get('after')
            # Tag/branch created/deleted
            if GITLAB_NULL_HASH in (before, after):
                log.debug(
                    'Triggered sync_versions.',
                    before=before,
                    after=after,
                )
                return self.sync_versions_response(self.project)
            # Normal push to master
            try:
                branch = self._normalize_ref(data["ref"])
                return self.get_response_push(self.project, [branch])
            except KeyError as exc:
                raise ParseError('Parameter "ref" is required') from exc

        if self.project.external_builds_enabled and event == GITLAB_MERGE_REQUEST:
            if not integration.secret:
                return Response(
                    {"detail": self.missing_secret_for_pr_events_msg},
                    status=HTTP_400_BAD_REQUEST,
                )

            if action in [
                GITLAB_MERGE_REQUEST_OPEN,
                GITLAB_MERGE_REQUEST_REOPEN,
                GITLAB_MERGE_REQUEST_UPDATE,
            ]:
                # Handle open, update, reopen merge_request event.
                return self.get_external_version_response(self.project)

            if action in [GITLAB_MERGE_REQUEST_CLOSE, GITLAB_MERGE_REQUEST_MERGE]:
                # Handle merge and close merge_request event.
                return self.get_closed_external_version_response(self.project)
        return None

    def _normalize_ref(self, ref):
        pattern = re.compile(r'^refs/(heads|tags)/')
        return pattern.sub('', ref)


class BitbucketWebhookView(WebhookMixin, APIView):

    """
    Webhook consumer for Bitbucket.

    Accepts webhook events from Bitbucket, 'repo:push' events trigger builds.

    Expects the following JSON::

        {
            "push": {
                "changes": [{
                    "new": {
                        "name": "branch-name",
                        ...
                    },
                    "old" {
                        "name": "branch-name",
                        ...
                    },
                    ...
                }],
                ...
            },
            ...
        }

    See full payload here:

    - https://confluence.atlassian.com/bitbucket/event-payloads-740262817.html#EventPayloads-Push
    """

    integration_type = Integration.BITBUCKET_WEBHOOK

    def handle_webhook(self):
        """
        Handle Bitbucket events for push.

        Bitbucket doesn't have a separate event for creation/deletion, instead
        it sets the new attribute (null if it is a deletion) and the old
        attribute (null if it is a creation).
        """
        event = self.request.headers.get(BITBUCKET_EVENT_HEADER, BITBUCKET_PUSH)
        log.bind(webhook_event=event)
        webhook_bitbucket.send(
            Project,
            project=self.project,
            data=self.request.data,
            event=event,
        )

        # NOTE: we can't call `self.update_default_branch` here because
        # BitBucket does not tell us what is the `default_branch` for a
        # repository in these incoming webhooks.

        if event == BITBUCKET_PUSH:
            try:
                data = self.request.data
                changes = data['push']['changes']
                branches = []
                for change in changes:
                    old = change['old']
                    new = change['new']
                    # Normal push to master
                    if old is not None and new is not None:
                        branches.append(new['name'])
                # BitBuck returns an array of changes rather than
                # one webhook per change. If we have at least one normal push
                # we don't trigger the sync versions, because that
                # will be triggered with the normal push.
                if branches:
                    return self.get_response_push(
                        self.project,
                        branches,
                    )
                log.debug("Triggered sync_versions.")
                return self.sync_versions_response(self.project)
            except KeyError as exc:
                raise ParseError("Invalid request") from exc
        return None

    def is_payload_valid(self):
        """
        BitBucket use a HMAC hexdigest hash to sign the payload.

        It is sent in the request's header.

        See https://support.atlassian.com/bitbucket-cloud/docs/manage-webhooks/#Secure-webhooks.
        """
        signature = self.request.headers.get(BITBUCKET_SIGNATURE_HEADER)
        secret = self.get_integration().secret
        if not secret:
            log.debug("Skipping payload signature validation.")
            return True
        if not signature:
            return False
        msg = self.request.body.decode()
        digest = WebhookMixin.get_digest(secret, msg)
        result = hmac.compare_digest(
            b"sha256=" + digest.encode(),
            signature.encode(),
        )
        return result


class IsAuthenticatedOrHasToken(permissions.IsAuthenticated):

    """
    Allow authenticated users and requests with token auth through.

    This does not check for instance-level permissions, as the check uses
    methods from the view to determine if the token matches.
    """

    def has_permission(self, request, view):
        has_perm = super().has_permission(request, view)
        return has_perm or 'token' in request.data


class APIWebhookView(WebhookMixin, APIView):

    """
    API webhook consumer.

    Expects the following JSON::

        {
            "branches": ["master"],
            "default_branch": "main"
        }
    """

    integration_type = Integration.API_WEBHOOK
    permission_classes = [IsAuthenticatedOrHasToken]

    def get_project(self, **kwargs):
        """
        Get authenticated user projects, or token authed projects.

        Allow for a user to either be authed to receive a project, or require
        the integration token to be specified as a POST argument.
        """
        # If the user is not an admin of the project, fall back to token auth
        if self.request.user.is_authenticated:
            try:
                return (
                    Project.objects.for_admin_user(
                        self.request.user,
                    ).get(**kwargs)
                )
            except Project.DoesNotExist:
                pass
        # Recheck project and integration relationship during token auth check
        token = self.request.data.get('token')
        if token:
            integration = self.get_integration()
            obj = Project.objects.get(**kwargs)
            is_valid = integration.project == obj and constant_time_compare(
                token, getattr(integration, "token", "")
            )
            if is_valid:
                return obj
        raise Project.DoesNotExist()

    def handle_webhook(self):
        try:
            branches = self.request.data.get(
                'branches',
                [self.project.get_default_branch()],
            )
            default_branch = self.request.data.get("default_branch", None)
            if isinstance(branches, str):
                branches = [branches]

            if default_branch and isinstance(default_branch, str):
                self.update_default_branch(default_branch)

            return self.get_response_push(self.project, branches)
        except TypeError as exc:
            raise ParseError("Invalid request") from exc

    def is_payload_valid(self):
        """
        Generic webhooks don't have payload validation.

        We use basic auth or token auth to validate that the user has access to
        the project and integration (get_project() method).
        """
        return True


class WebhookView(APIView):

    """
    Main webhook view for webhooks with an ID.

    The handling of each view is handed off to another view. This should only
    ever get webhook requests for established webhooks on our side. The other
    views can receive webhooks for unknown webhooks, as all legacy webhooks will
    be.

    .. warning::
        We're turning off Authentication for this view.
        This fixes a bug where we were double-authenticating these views,
        because of the way we're passing the request along to the subviews.

        If at any time we add real logic to this view,
        it will be completely unauthenticated.
    """

    authentication_classes = []

    VIEW_MAP = {
        Integration.GITHUB_WEBHOOK: GitHubWebhookView,
        Integration.GITLAB_WEBHOOK: GitLabWebhookView,
        Integration.BITBUCKET_WEBHOOK: BitbucketWebhookView,
        Integration.API_WEBHOOK: APIWebhookView,
    }

    def post(self, request, project_slug, integration_pk):
        """Set up webhook post view with request and project objects."""
        # WARNING: this is a hack to allow us access to `request.body` later.
        # Due to a limitation of DRF, we can't access `request.body`
        # after accessing `request.data`.
        # By accessing `request.body` we are able to access `request.body` and
        # `request.data` later without any problem (mostly black magic).
        # See #4940 for more background.
        request.body  # noqa
        integration = get_object_or_404(
            Integration,
            project__slug=project_slug,
            pk=integration_pk,
        )
        view_cls = self.VIEW_MAP[integration.integration_type]
        view = view_cls.as_view(integration=integration)
        # DRF uses ``rest_framework.request.Request`` and Django expects
        # ``django.http.HttpRequest``
        # https://www.django-rest-framework.org/api-guide/requests/
        # https://github.com/encode/django-rest-framework/pull/5771#issuecomment-362815342
        return view(request._request, project_slug)
