# -*- coding: utf-8 -*-
"""Tasks for OAuth services."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging

from allauth.socialaccount.providers import registry as allauth_registry
from django.contrib.auth.models import User

from readthedocs.core.utils.tasks import PublicTask, user_id_matches
from readthedocs.oauth.notifications import (
    AttachWebhookNotification,
    InvalidProjectWebhookNotification,
)
from readthedocs.projects.models import Project
from readthedocs.worker import app

from .services import registry

log = logging.getLogger(__name__)


@PublicTask.permission_check(user_id_matches)
@app.task(queue='web', base=PublicTask)
def sync_remote_repositories(user_id):
    user = User.objects.get(pk=user_id)
    for service_cls in registry:
        for service in service_cls.for_user(user):
            service.sync()


@app.task(queue='web')
def attach_webhook(project_pk, user_pk):
    """
    Add post-commit hook on project import.

    This is a brute force approach to add a webhook to a repository. We try
    all accounts until we set up a webhook. This should remain around for legacy
    connections -- that is, projects that do not have a remote repository them
    and were not set up with a VCS provider.
    """
    project = Project.objects.get(pk=project_pk)
    user = User.objects.get(pk=user_pk)
    project_notification = InvalidProjectWebhookNotification(
        context_object=project,
        user=user,
        success=False,
    )

    for service_cls in registry:
        if service_cls.is_project_service(project):
            service = service_cls
            break
    else:
        log.warning('There are no registered services in the application.')
        project_notification.send()
        return None

    provider = allauth_registry.by_id(service.adapter.provider_id)
    notification = AttachWebhookNotification(
        context_object=provider,
        extra_context={'project': project},
        user=user,
        success=None,
    )

    user_accounts = service.for_user(user)
    for account in user_accounts:
        success, __ = account.setup_webhook(project)
        if success:
            notification.success = True
            notification.send()

            project.has_valid_webhook = True
            project.save()
            return True

    # No valid account found
    if user_accounts:
        notification.success = False
        notification.reason = AttachWebhookNotification.NO_PERMISSIONS
    else:
        notification.success = False
        notification.reason = AttachWebhookNotification.NO_ACCOUNTS

    project_notification.send()
    notification.send()
    return False
