"""Signal handling for core app."""

import structlog
from corsheaders import signals
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import Signal, receiver
from rest_framework.permissions import SAFE_METHODS
from simple_history.models import HistoricalRecords
from simple_history.signals import pre_create_historical_record

from readthedocs.analytics.utils import get_client_ip
from readthedocs.builds.models import Version
from readthedocs.core.unresolver import unresolve
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)

ALLOWED_URLS = [
    '/api/v2/footer_html',
    '/api/v2/search',
    '/api/v2/docsearch',
    '/api/v2/embed',
    '/api/v3/embed',
]

webhook_github = Signal()
webhook_gitlab = Signal()
webhook_bitbucket = Signal()

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
    * The version is public

    .. note::

       Requests from the sustainability API are always allowed
       if the donate app is installed.

    :returns: `True` when a request should be given CORS access.
    """
    if 'HTTP_ORIGIN' not in request.META or request.method not in SAFE_METHODS:
        return False

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
            if unresolved is None:
                # NOTE: Embed APIv3 now supports external sites. In that case
                # ``unresolve()`` will return None and we want to allow it
                # since the target is a public project.
                return True

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

    return False


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_projects_and_organizations(sender, instance, *args, **kwargs):
    """
    Delete projects and organizations where the user is the only owner.

    We delete projects that don't belong to an organization first,
    then full organizations.
    """
    user = instance

    for project in Project.objects.single_owner(user):
        project.delete()

    for organization in Organization.objects.single_owner(user):
        organization.delete()


@receiver(pre_create_historical_record)
def add_extra_historical_fields(sender, **kwargs):
    history_instance = kwargs['history_instance']
    if not history_instance:
        return

    history_user = kwargs['history_user']
    if history_user:
        history_instance.extra_history_user_id = history_user.id
        history_instance.extra_history_user_username = history_user.username

    request = getattr(HistoricalRecords.context, 'request', None)
    if request:
        history_instance.extra_history_ip = get_client_ip(request)
        history_instance.extra_history_browser = request.headers.get('User-Agent')


signals.check_request_enabled.connect(decide_if_cors)
