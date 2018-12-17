"""Endpoints integrating with Github, Bitbucket, and other webhooks."""

import json
import logging
import re

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.core.signals import (
    webhook_bitbucket,
    webhook_github,
    webhook_gitlab,
)
from readthedocs.core.views.hooks import build_branches, sync_versions
from readthedocs.integrations.models import HttpExchange, Integration
from readthedocs.integrations.utils import normalize_request_payload
from readthedocs.projects.models import Project

from ..authentication import CsrfExemptSessionAuthentication


log = logging.getLogger(__name__)

GITHUB_EVENT_HEADER = 'HTTP_X_GITHUB_EVENT'
GITHUB_PUSH = 'push'
GITHUB_CREATE = 'create'
GITHUB_DELETE = 'delete'
GITLAB_PUSH = 'push'
GITLAB_NULL_HASH = '0' * 40
GITLAB_TAG_PUSH = 'tag_push'
BITBUCKET_EVENT_HEADER = 'HTTP_X_EVENT_KEY'
BITBUCKET_PUSH = 'repo:push'


class WebhookMixin:

    """Base class for Webhook mixins."""

    permission_classes = (permissions.AllowAny,)
    renderer_classes = (JSONRenderer,)
    integration = None
    integration_type = None

    def post(self, request, project_slug):
        """Set up webhook post view with request and project objects."""
        self.request = request
        self.project = None
        self.data = self.get_data()
        try:
            self.project = self.get_project(slug=project_slug)
            if not Project.objects.is_active(self.project):
                resp = {'detail': 'This project is currently disabled'}
                return Response(resp, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Project.DoesNotExist:
            raise NotFound('Project not found')
        resp = self.handle_webhook()
        if resp is None:
            log.info('Unhandled webhook event')
            resp = {'detail': 'Unhandled webhook event'}
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
        """Normalize posted data."""
        return normalize_request_payload(self.request)

    def handle_webhook(self):
        """Handle webhook payload."""
        raise NotImplementedError

    def get_integration(self):
        """
        Get or create an inbound webhook to track webhook requests.

        We shouldn't need this, but to support legacy webhooks, we can't assume
        that a webhook has ever been created on our side. Most providers don't
        pass the webhook ID in either, so we default to just finding *any*
        integration from the provider. This is not ideal, but the
        :py:class:`WebhookView` view solves this by performing a lookup on the
        integration instead of guessing.
        """
        # `integration` can be passed in as an argument to `as_view`, as it is
        # in `WebhookView`
        if self.integration is not None:
            return self.integration
        integration, _ = Integration.objects.get_or_create(
            project=self.project,
            integration_type=self.integration_type,
        )
        return integration

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
        :param branches: List of branch names to build
        :type branches: list(str)
        """
        to_build, not_building = build_branches(project, branches)
        if not_building:
            log.info(
                'Skipping project branches: project=%s branches=%s',
                project,
                branches,
            )
        triggered = True if to_build else False
        return {
            'build_triggered': triggered,
            'project': project.slug,
            'versions': list(to_build),
        }

    def sync_versions(self, project):
        version = sync_versions(project)
        return {
            'build_triggered': False,
            'project': project.slug,
            'versions': [version],
        }


class GitHubWebhookView(WebhookMixin, APIView):

    """
    Webhook consumer for GitHub.

    Accepts webhook events from GitHub, 'push' events trigger builds. Expects the
    webhook event type will be included in HTTP header ``X-GitHub-Event``, and
    we will have a JSON payload.

    Expects the following JSON::

        {
            "ref": "branch-name",
            ...
        }

    See full payload here:

    - https://developer.github.com/v3/activity/events/types/#pushevent
    - https://developer.github.com/v3/activity/events/types/#createevent
    - https://developer.github.com/v3/activity/events/types/#deleteevent
    """

    integration_type = Integration.GITHUB_WEBHOOK

    def get_data(self):
        if self.request.content_type == 'application/x-www-form-urlencoded':
            try:
                return json.loads(self.request.data['payload'])
            except (ValueError, KeyError):
                pass
        return super().get_data()

    def handle_webhook(self):
        # Get event and trigger other webhook events
        event = self.request.META.get(GITHUB_EVENT_HEADER, GITHUB_PUSH)
        webhook_github.send(
            Project,
            project=self.project,
            data=self.data,
            event=event,
        )
        # Handle push events and trigger builds
        if event == GITHUB_PUSH:
            try:
                branches = [self._normalize_ref(self.data['ref'])]
                return self.get_response_push(self.project, branches)
            except KeyError:
                raise ParseError('Parameter "ref" is required')
        if event in (GITHUB_CREATE, GITHUB_DELETE):
            return self.sync_versions(self.project)
        return None

    def _normalize_ref(self, ref):
        pattern = re.compile(r'^refs/(heads|tags)/')
        return pattern.sub('', ref)


class GitLabWebhookView(WebhookMixin, APIView):

    """
    Webhook consumer for GitLab.

    Accepts webhook events from GitLab, 'push' events trigger builds.

    Expects the following JSON::

        {
            "before": "95790bf891e76fee5e1747ab589903a6a1f80f22",
            "after": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
            "object_kind": "push",
            "ref": "branch-name",
            ...
        }

    See full payload here:

    - https://docs.gitlab.com/ce/user/project/integrations/webhooks.html#push-events
    - https://docs.gitlab.com/ce/user/project/integrations/webhooks.html#tag-events
    """

    integration_type = Integration.GITLAB_WEBHOOK

    def handle_webhook(self):
        """
        Handle GitLab events for push and tag_push.

        GitLab doesn't have a separate event for creation/deletion,
        instead, it sets the before/after field to
        0000000000000000000000000000000000000000 ('0' * 40)
        """
        event = self.request.data.get('object_kind', GITLAB_PUSH)
        webhook_gitlab.send(
            Project,
            project=self.project,
            data=self.request.data,
            event=event,
        )
        # Handle push events and trigger builds
        if event in (GITLAB_PUSH, GITLAB_TAG_PUSH):
            data = self.request.data
            before = data['before']
            after = data['after']
            # Tag/branch created/deleted
            if GITLAB_NULL_HASH in (before, after):
                return self.sync_versions(self.project)
            # Normal push to master
            try:
                branches = [self._normalize_ref(data['ref'])]
                return self.get_response_push(self.project, branches)
            except KeyError:
                raise ParseError('Parameter "ref" is required')
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
        Handle BitBucket events for push.

        BitBucket doesn't have a separate event for creation/deletion, instead
        it sets the new attribute (null if it is a deletion) and the old
        attribute (null if it is a creation).
        """
        event = self.request.META.get(BITBUCKET_EVENT_HEADER, BITBUCKET_PUSH)
        webhook_bitbucket.send(
            Project,
            project=self.project,
            data=self.request.data,
            event=event,
        )
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
                    return self.get_response_push(self.project, branches)
                return self.sync_versions(self.project)
            except KeyError:
                raise ParseError('Invalid request')
        return None


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
            "branches": ["master"]
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
            is_valid = (
                integration.project == obj and
                token == getattr(integration, 'token', None)
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
            if isinstance(branches, str):
                branches = [branches]
            return self.get_response_push(self.project, branches)
        except TypeError:
            raise ParseError('Invalid request')


class WebhookView(APIView):

    """
    Main webhook view for webhooks with an ID.

    The handling of each view is handed off to another view. This should only
    ever get webhook requests for established webhooks on our side. The other
    views can receive webhooks for unknown webhooks, as all legacy webhooks will
    be.
    """

    # We want to avoid CSRF checking when authenticating by user/password on
    # this API endpoint so we can make a request like:
    # curl -X POST -d "branches=branch" -u user:pass -e URL /api/v2/webhook/test-builds/{pk}/
    authentication_classes = [CsrfExemptSessionAuthentication]

    VIEW_MAP = {
        Integration.GITHUB_WEBHOOK: GitHubWebhookView,
        Integration.GITLAB_WEBHOOK: GitLabWebhookView,
        Integration.BITBUCKET_WEBHOOK: BitbucketWebhookView,
        Integration.API_WEBHOOK: APIWebhookView,
    }

    def post(self, request, project_slug, integration_pk):
        """Set up webhook post view with request and project objects."""
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
