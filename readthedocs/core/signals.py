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
from readthedocs.projects.utils import get_projects_only_owner

log = logging.getLogger(__name__)

WHITELIST_URLS = [
    '/api/v2/footer_html',
    '/api/v2/search',
    '/api/v2/docsearch',
    '/api/v2/sustainability',
]

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

    # Don't do domain checking for this API for now
    if request.path_info.startswith('/api/v2/sustainability'):
        return True

    # Don't do domain checking for APIv2 when the Domain is known
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
def delete_projects_and_organizations(sender, instance, *args, **kwargs):
    user = instance
    projects = get_projects_only_owner(user)

    # Here we count the users list from the organization that the user belong
    # Then exclude the organizations where there are more than one user
    oauth_organizations = (
        RemoteOrganization.objects
        .annotate(num_users=Count('users'))
        .filter(users=instance.id, num_users=1)
    )

    projects.delete()
    oauth_organizations.delete()


signals.check_request_enabled.connect(decide_if_cors)
