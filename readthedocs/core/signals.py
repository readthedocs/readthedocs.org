"""Signal handling for core app."""

from __future__ import absolute_import

import logging

from corsheaders import signals
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import Signal
from django.db.models import Q, Count
from django.dispatch import receiver
from future.backports.urllib.parse import urlparse

from readthedocs.projects.models import Project, Domain

log = logging.getLogger(__name__)

WHITELIST_URLS = ['/api/v2/footer_html', '/api/v2/search',
                  '/api/v2/docsearch', '/api/v2/sustainability']


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
            Q(domain__icontains=host),
            Q(project=project) | Q(project__subprojects__child=project)
        )
        if domain.exists():
            return True

    return False


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_projects_and_organizations(sender, instance, *args, **kwargs):
    # Here we count the owner list from the projects that the user own
    # Then exclude the projects where there are more than one owner
    projects = instance.projects.all().annotate(num_users=Count('users')).exclude(num_users__gt=1)

    # Here we count the users list from the organization that the user belong
    # Then exclude the organizations where there are more than one user
    oauth_organizations = (instance.oauth_organizations.annotate(num_users=Count('users'))
                                                       .exclude(num_users__gt=1))

    projects.delete()
    oauth_organizations.delete()


signals.check_request_enabled.connect(decide_if_cors)
