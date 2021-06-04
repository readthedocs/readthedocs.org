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

from readthedocs.builds.models import Version
from readthedocs.core.unresolver import unresolve
from readthedocs.projects.models import Domain, Project


log = logging.getLogger(__name__)

ALLOWED_URLS = [
    '/api/v2/footer_html',
    '/api/v2/search',
    '/api/v2/docsearch',
    '/api/v2/sustainability',
]

webhook_github = Signal(providing_args=['project', 'data', 'event'])
webhook_gitlab = Signal(providing_args=['project', 'data', 'event'])
webhook_bitbucket = Signal(providing_args=['project', 'data', 'event'])

pre_collectstatic = Signal()
post_collectstatic = Signal()


def decide_if_cors(sender, request, **kwargs):  # pylint: disable=unused-argument
    """
    Decide whether a request should be given CORS access.

    This checks that:
    * The URL is whitelisted against our CORS-allowed domains
    * The Domain exists in our database, and belongs to the project being queried.

    Returns True when a request should be given CORS access.
    """
    if 'HTTP_ORIGIN' not in request.META:
        return False
    host = urlparse(request.META['HTTP_ORIGIN']).netloc.split(':')[0]

    # Don't do domain checking for this API for now
    if request.path_info.startswith('/api/v2/sustainability'):
        return True

    # Don't do domain checking for APIv2 when the Domain is known
    if request.path_info.startswith('/api/v2/') and request.method in SAFE_METHODS:
        domain = Domain.objects.filter(domain__icontains=host)
        if domain.exists():
            return True

    # Check for Embed API, allowing CORS on public projects
    # since they are already public
    if request.path_info.startswith('/api/v2/embed'):
        url = request.GET.get('url')
        if url:
            unresolved = unresolve(url)
            project = unresolved.project
            version_slug = unresolved.version_slug
        else:
            project_slug = request.GET.get('project', None)
            version_slug = request.GET.get('version', None)
            project = Project.objects.filter(slug=project_slug).first()

        if project and version_slug:
            # This is from IsAuthorizedToViewVersion,
            # we should abstract is a bit perhaps?
            has_access = (
                Version.objects
                .public(
                    user=request.user,
                    project=project,
                    only_active=False,
                )
                .filter(slug=version_slug)
                .exists()
            )
            if has_access:
                return True

        return False

    valid_url = False
    for url in ALLOWED_URLS:
        if request.path_info.startswith(url):
            valid_url = True
            break

    if valid_url:
        project_slug = request.GET.get('project', None)
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            log.warning(
                'Invalid project passed to domain. [%s:%s]',
                project_slug,
                host,
            )
            return False

        domain = Domain.objects.filter(
            Q(domain__icontains=host),
            Q(project=project) | Q(project__subprojects__child=project),
        )
        if domain.exists():
            return True

    return False


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_projects(sender, instance, *args, **kwargs):
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

    projects.delete()


signals.check_request_enabled.connect(decide_if_cors)
