# -*- coding: utf-8 -*-

import logging

from django.db.models import Q

from readthedocs.projects.models import Project
from readthedocs.projects.notifications import DeprecatedWebhookEndpointNotification

log = logging.getLogger(__name__)


def notify_deprecated_endpoint(function):
    """
    Decorator to notify owners that the endpoint is DEPRECATED.
    """
    def wrap(request, *args, project_id_or_slug=None, **kwargs):
        try:
            project = Project.objects.get(
                Q(pk=project_id_or_slug) | Q(slug=project_id_or_slug),
            )
        except (Project.DoesNotExist, ValueError):
            log.info('Project not found: slug=%s', project_id_or_slug)

        # Send one notification to each owner of the project
        for user in project.users.all():
            notification = DeprecatedWebhookEndpointNotification(
                project,
                request,
                user,
            )
            notification.send()
        return function(request, *args, project_id_or_slug, **kwargs)

    return wrap
