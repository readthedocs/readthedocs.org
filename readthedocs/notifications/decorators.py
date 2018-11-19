# -*- coding: utf-8 -*-

import logging

from django.db.models import Q
from django.http import HttpRequest

from readthedocs.projects.models import Project
from readthedocs.projects.notifications import DeprecatedWebhookEndpointNotification

log = logging.getLogger(__name__)


def notify_deprecated_endpoint(function):
    """
    Decorator to notify owners that the endpoint is DEPRECATED.
    """
    def wrap(*args, **kwargs):
        # Called from ``generic_build``
        project_id_or_slug = kwargs.get('project_id_or_slug')

        if project_id_or_slug:
            projects = Project.objects.filter(
                Q(pk=project_id_or_slug) | Q(slug=project_id_or_slug),
            )
        else:
            # Called from ``_build_url``
            projects = args[1]  # ``projects`` argument

        if projects:
            for project in projects:
                # Send one notification to each owner of the project
                for user in project.users.all():
                    notification = DeprecatedWebhookEndpointNotification(
                        project,
                        HttpRequest(),
                        user,
                    )
                    notification.send()
        else:
            log.info('Projects not found when hitting deprecated webhook')

        return function(*args, **kwargs)

    return wrap
