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

WHITELIST_URLS = [
    '/api/v2/footer_html',
    '/api/v2/search',
    '/api/v2/docsearch',
]

# Don't do domain checking on these URL's
ANY_DOMAIN_WHITELIST_URLS = [
    '/api/v2/sustainability',
    '/api/v2/embed',
    '/_/api/v2/embed',

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

    for url in ANY_DOMAIN_WHITELIST_URLS:
        if request.path_info.startswith(url):
            return True

    # Don't do additional domain checking for APIv2 when the Domain is known
    if request.path_info.startswith('/api/v2/') and request.method in SAFE_METHODS:
        domain = Domain.objects.filter(domain__icontains=host)
        if domain.exists():
            return True

    valid_url = False
    for url in WHITELIST_URLS:
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
