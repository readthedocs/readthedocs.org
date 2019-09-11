# -*- coding: utf-8 -*-

"""Signal handling for core app."""

import logging
from urllib.parse import urlparse

from corsheaders import signals
from django.conf import settings
from django.db.models import Count, Q
from django.db.models.signals import pre_delete
from django.dispatch import Signal, receiver
from rest_framework.permissions import SAFE_METHODS

from readthedocs.oauth.models import RemoteOrganization
from readthedocs.projects.models import Domain, Project


log = logging.getLogger(__name__)

webhook_github = Signal(providing_args=['project', 'data', 'event'])
webhook_gitlab = Signal(providing_args=['project', 'data', 'event'])
webhook_bitbucket = Signal(providing_args=['project', 'data', 'event'])


def decide_if_cors(sender, request, **kwargs):  # pylint: disable=unused-argument
    """
    Decide whether a request should be given CORS access.

    This checks that the URL is under ``/api/`` and it's a safe method.

    Returns ``True`` when a request should be given CORS access.
    """
    return all([
        request.method in SAFE_METHODS,
        request.path_info.startswith('/api/'),
    ])


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_projects_and_organizations(sender, instance, *args, **kwargs):
    # Here we count the owner list from the projects that the user own
    # Then exclude the projects where there are more than one owner
    # Add annotate before filter
    # https://github.com/rtfd/readthedocs.org/pull/4577
    # https://docs.djangoproject.com/en/2.1/topics/db/aggregation/#order-of-annotate-and-filter-clauses # noqa
    projects = (
        Project.objects.annotate(num_users=Count('users')
                                 ).filter(users=instance.id
                                          ).exclude(num_users__gt=1)
    )

    # Here we count the users list from the organization that the user belong
    # Then exclude the organizations where there are more than one user
    oauth_organizations = (
        RemoteOrganization.objects.annotate(num_users=Count('users')
                                            ).filter(users=instance.id
                                                     ).exclude(num_users__gt=1)
    )

    projects.delete()
    oauth_organizations.delete()


signals.check_request_enabled.connect(decide_if_cors)
