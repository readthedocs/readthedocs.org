"""Signal handling for core app."""

from __future__ import absolute_import

import logging

from corsheaders import signals
from django.dispatch import Signal
from future.backports.urllib.parse import urlparse

from readthedocs.projects.models import Project, Domain


log = logging.getLogger(__name__)

WHITELIST_URLS = ['/api/v2/footer_html', '/api/v2/search', '/api/v2/docsearch']


webhook_github = Signal(providing_args=['project', 'data', 'event'])
webhook_gitlab = Signal(providing_args=['project', 'data', 'event'])
webhook_bitbucket = Signal(providing_args=['project', 'data', 'event'])


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
    valid_url = False
    for url in WHITELIST_URLS:
        if request.path_info.startswith(url):
            valid_url = True

    if valid_url:
        project_slug = request.GET.get('project', None)
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            log.warning(
                'Invalid project passed to domain. [{project}:{domain}'.format(
                    project=project_slug,
                    domain=host,
                )
            )
            return False

        domain = Domain.objects.filter(
            domain__icontains=host,
            project=project
        )
        if domain.exists():
            return True

    return False

signals.check_request_enabled.connect(decide_if_cors)
