from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.exceptions import ParseError

from django.shortcuts import get_object_or_404
from django.http import Http404

from readthedocs.core.views.hooks import build_branches
from readthedocs.core.signals import (webhook_github, webhook_bitbucket,
                                      webhook_gitlab)
from readthedocs.projects.models import Project


GITHUB_PUSH = 'push'
GITLAB_PUSH = 'push'
BITBUCKET_PUSH = 'repo:push'


class WebhookMixin(object):

    permission_classes = (permissions.AllowAny,)
    renderer_classes = (JSONRenderer,)

    def post(self, request, project_slug, format=None):
        try:
            project = Project.objects.get(slug=project_slug)
            resp = self.handle_webhook(request, project, request.data)
        except Project.DoesNotExist:
            raise Http404('Project does not exist')
        return Response(resp)

    def handle_webhook(self, project, branch, event=GITHUB_PUSH, data=None):
        """Handle webhook payload

        If a build is triggered from this method, return a JSON response with
        the following::

            {
                "build_triggered": true,
                "project": "project_name",
                "versions": [...]
            }
        """
        raise NotImplemented


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

    If a build is triggered, this will return JSON with the following::

        {
            "build_triggered": true,
            "project": "project_name",
            "versions": [...]
        }
    """

    def handle_webhook(self, request, project, data=None):
        # Get event and trigger other webhook events
        event = request.META.get('HTTP_X_GITHUB_EVENT', 'push')
        webhook_github.send(Project, project=project, data=data, event=event)
        # Handle push events and trigger builds
        try:
            branches = [request.data['ref'].replace('refs/heads/', '')]
        except KeyError:
            raise ParseError('Parameter "ref" is required')
        if event == GITHUB_PUSH:
            to_build, not_building = build_branches(project, branches)
            triggered = True if to_build else False
            return {'build_triggered': triggered,
                    'project': project.slug,
                    'versions': to_build}
        return {'build_triggered': false}


class GitLabWebhookView(WebhookMixin, APIView):

    """Webhook consumer for GitLab

    Accepts webhook events from GitLab, 'push' events trigger builds.

    Expects the following JSON::

        {
            "object_kind": "push",
            "ref": "branch-name",
            ...
        }

    If a build is triggered, this will return JSON with the following::

        {
            "build_triggered": true,
            "project": "project_name",
            "versions": [...]
        }
    """

    def handle_webhook(self, request, project, data=None):
        # Get event and trigger other webhook events
        event = data.get('object_kind', GITLAB_PUSH)
        webhook_gitlab.send(Project, project=project, data=data, event=event)
        # Handle push events and trigger builds
        try:
            branches = [request.data['ref'].replace('refs/heads/', '')]
        except KeyError:
            raise ParseError('Parameter "ref" is required')
        if event == GITLAB_PUSH:
            to_build, not_building = build_branches(project, branches)
            triggered = True if to_build else False
            return {'build_triggered': triggered,
                    'project': project.slug,
                    'versions': to_build}
        return {'build_triggered': false}


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

    def handle_webhook(self, request, project, data=None):
        # Get event and trigger other webhook events
        event = request.META.get('HTTP_X_EVENT_KEY', BITBUCKET_PUSH)
        webhook_bitbucket.send(Project, project=project, data=data, event=event)
        # Handle push events and trigger builds
        if event == BITBUCKET_PUSH:
            try:
                changes = data['push']['changes']
                branches = [change['new']['name']
                            for change in changes]
            except KeyError:
                raise ParseError('Invalid request')
            to_build, not_building = build_branches(project, branches)
            triggered = True if to_build else False
            return {'build_triggered': triggered,
                    'project': project.slug,
                    'versions': to_build}
        return {'build_triggered': false}
