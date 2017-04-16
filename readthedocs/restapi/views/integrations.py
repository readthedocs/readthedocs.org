import json
import logging

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ParseError, NotFound

from django.shortcuts import get_object_or_404
from django.http import Http404

from readthedocs.core.views.hooks import build_branches
from readthedocs.core.signals import (webhook_github, webhook_bitbucket,
                                      webhook_gitlab)
from readthedocs.integrations.models import HttpExchange
from readthedocs.integrations.utils import normalize_request_payload
from readthedocs.projects.models import Project


log = logging.getLogger(__name__)

GITHUB_PUSH = 'push'
GITLAB_PUSH = 'push'
BITBUCKET_PUSH = 'repo:push'


class WebhookMixin(object):

    permission_classes = (permissions.AllowAny,)
    renderer_classes = (JSONRenderer,)

    def post(self, request, project_slug, format=None):
        """Set up webhook post view with request and project objects"""
        self.request = request
        self.project = None
        try:
            self.project = Project.objects.get(slug=project_slug)
            resp = self.handle_webhook()
            if resp is None:
                log.info('Unhandled webhook event')
                resp = {'detail': 'Unhandled webhook event'}
            resp = Response(resp)
        except Project.DoesNotExist:
            raise NotFound('Project not found')
        return resp

    def finalize_response(self, req, *args, **kwargs):
        """If the project was set on POST, store an HTTP exchange"""
        resp = super(WebhookMixin, self).finalize_response(req, *args, **kwargs)
        if hasattr(self, 'project') and self.project:
            HttpExchange.objects.from_exchange(
                req,
                resp,
                related_object=self.project,
                payload=self.get_payload(),
            )
        return resp

    def handle_webhook(self):
        """Handle webhook payload"""
        raise NotImplementedError

    def get_payload(self):
        """Don't specify any special handling of the payload data

        The exchange will record ``request.data`` instead of assume any
        special handling of the payload data
        """
        return None

    def get_response_push(self, project, branches):
        """Build branches on push events and return API response

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
            log.info('Skipping project branches: project=%s branches=%s',
                     project, branches)
        triggered = True if to_build else False
        return {'build_triggered': triggered,
                'project': project.slug,
                'versions': list(to_build)}


class GitHubWebhookView(WebhookMixin, APIView):

    """Webhook consumer for GitHub

    Accepts webhook events from GitHub, 'push' events trigger builds. Expects the
    webhook event type will be included in HTTP header ``X-GitHub-Event``, and
    we will have a JSON payload.

    Expects the following JSON::

        {
            "ref": "branch-name",
            ...
        }
    """

    def get_payload(self):
        if self.request.content_type == 'application/x-www-form-urlencoded':
            try:
                return json.loads(self.request.data['payload'])
            except ValueError:
                pass
        return normalize_request_payload(self.request)

    def handle_webhook(self):
        data = self.get_payload()
        # Get event and trigger other webhook events
        event = self.request.META.get('HTTP_X_GITHUB_EVENT', 'push')
        webhook_github.send(Project, project=self.project,
                            data=data, event=event)
        # Handle push events and trigger builds
        if event == GITHUB_PUSH:
            try:
                branches = [data['ref'].replace('refs/heads/', '')]
                return self.get_response_push(self.project, branches)
            except KeyError:
                raise ParseError('Parameter "ref" is required')


class GitLabWebhookView(WebhookMixin, APIView):

    """Webhook consumer for GitLab

    Accepts webhook events from GitLab, 'push' events trigger builds.

    Expects the following JSON::

        {
            "object_kind": "push",
            "ref": "branch-name",
            ...
        }
    """

    def handle_webhook(self):
        # Get event and trigger other webhook events
        event = self.request.data.get('object_kind', GITLAB_PUSH)
        webhook_gitlab.send(Project, project=self.project,
                            data=self.request.data, event=event)
        # Handle push events and trigger builds
        if event == GITLAB_PUSH:
            try:
                branches = [self.request.data['ref'].replace('refs/heads/', '')]
                return self.get_response_push(self.project, branches)
            except KeyError:
                raise ParseError('Parameter "ref" is required')


class BitbucketWebhookView(WebhookMixin, APIView):

    """Webhook consumer for Bitbucket

    Accepts webhook events from Bitbucket, 'repo:push' events trigger builds.

    Expects the following JSON::

        {
            "push": {
                "changes": [{
                    "new": {
                        "name": "branch-name",
                        ...
                    },
                    ...
                }],
                ...
            },
            ...
        }
    """

    def handle_webhook(self):
        # Get event and trigger other webhook events
        event = self.request.META.get('HTTP_X_EVENT_KEY', BITBUCKET_PUSH)
        webhook_bitbucket.send(Project, project=self.project,
                               data=self.request.data, event=event)
        # Handle push events and trigger builds
        if event == BITBUCKET_PUSH:
            try:
                changes = self.request.data['push']['changes']
                branches = [change['new']['name']
                            for change in changes]
                return self.get_response_push(self.project, branches)
            except KeyError:
                raise ParseError('Invalid request')


class GenericWebhookView(WebhookMixin, APIView):

    """Generic webhook consumer

    Expects the following JSON::

        {
            "branches": ["master"]
        }
    """

    def handle_webhook(self):
        try:
            branches = list(self.request.data.get(
                'branches',
                [self.project.get_default_branch()]
            ))
            return self.get_response_push(self.project, branches)
        except TypeError:
            raise ParseError('Invalid request')
