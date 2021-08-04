"""Signal handling for core app."""

import logging
from urllib.parse import urlparse

from corsheaders import signals
from django.conf import settings
from django.db.models import Count, Q
from django.db.models.signals import pre_delete
from django.dispatch import Signal, receiver
from rest_framework.permissions import SAFE_METHODS
from simple_history.signals import pre_create_historical_record

from readthedocs.builds.models import Version
from readthedocs.core.unresolver import unresolve
from readthedocs.projects.models import Domain, Project

log = logging.getLogger(__name__)

ALLOWED_URLS = [
    '/api/v2/footer_html',
    '/api/v2/search',
    '/api/v2/docsearch',
    '/api/v2/embed',
]

webhook_github = Signal(providing_args=['project', 'data', 'event'])
webhook_gitlab = Signal(providing_args=['project', 'data', 'event'])
webhook_bitbucket = Signal(providing_args=['project', 'data', 'event'])

pre_collectstatic = Signal()
post_collectstatic = Signal()


def _has_donate_app():
    """
    Check if the current app has the sustainability API.

    This is a separate function so it's easy to mock.
    """
    return 'readthedocsext.donate' in settings.INSTALLED_APPS


def decide_if_cors(sender, request, **kwargs):  # pylint: disable=unused-argument
    """
    Decide whether a request should be given CORS access.

    Allow the request if:

    * It's a safe HTTP method
    * The origin is in ALLOWED_URLS
    * The URL is owned by the project that they are requesting data from
    * The version is public or the domain is linked to the project
      (except for the embed API).

    .. note::

       Requests from the sustainability API are always allowed
       if the donate app is installed.

    :returns: `True` when a request should be given CORS access.
    """
    if 'HTTP_ORIGIN' not in request.META or request.method not in SAFE_METHODS:
        return False

    host = urlparse(request.META['HTTP_ORIGIN']).netloc.split(':')[0]

    # Always allow the sustainability API,
    # it's used only on .org to check for ad-free users.
    if _has_donate_app() and request.path_info.startswith('/api/v2/sustainability'):
        return True

    valid_url = None
    for url in ALLOWED_URLS:
        if request.path_info.startswith(url):
            valid_url = url
            break

    if valid_url:
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
            is_public = (
                Version.objects
                .public(
                    project=project,
                    only_active=False,
                )
                .filter(slug=version_slug)
                .exists()
            )
            # Allowing CORS on public versions,
            # since they are already public.
            if is_public:
                return True

            # Don't check for known domains for the embed api.
            # It gives a lot of information,
            # we should use a list of trusted domains from the user.
            if valid_url == '/api/v2/embed':
                return False

            # Or allow if they have a registered domain
            # linked to that project.
            domain = Domain.objects.filter(
                Q(domain__iexact=host),
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


@receiver(pre_create_historical_record)
def add_extra_historical_fields(sender, **kwargs):
    history_instance = kwargs['history_instance']
    history_user = kwargs['history_user']
    if history_instance and history_user:
        history_instance.extra_history_user_id = history_user.id
        history_instance.extra_history_user_username = history_user.username


signals.check_request_enabled.connect(decide_if_cors)
