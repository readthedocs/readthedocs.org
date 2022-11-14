"""Signal handling for core app."""

import requests
import structlog
from allauth.account.signals import email_confirmed
from corsheaders import signals
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import Signal, receiver
from rest_framework.permissions import SAFE_METHODS
from simple_history.models import HistoricalRecords
from simple_history.signals import pre_create_historical_record

from readthedocs.analytics.utils import get_client_ip
from readthedocs.builds.models import Version
from readthedocs.core.models import UserProfile
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


@receiver(email_confirmed)
def process_email_confirmed(request, email_address, **kwargs):
    """
    Steps to take after a users email address is confirmed.

    We currently:

    * Subscribe the user to the mailing list if they set this in their signup.
    * Add them to a drip campaign for new users in the new user group.
    """

    # email_address is an object
    # https://github.com/pennersr/django-allauth/blob/6315e25/allauth/account/models.py#L15
    user = email_address.user
    profile = UserProfile.objects.filter(user=user).first()
    if profile and profile.mailing_list:
        # TODO: Unsubscribe users if they unset `mailing_list`.
        log.bind(
            email=email_address.email,
            username=user.username,
        )
        log.info("Subscribing user to newsletter and onboarding group.")

        # Try subscribing user to a group, then fallback to normal subscription API
        url = settings.MAILERLITE_API_ONBOARDING_GROUP_URL
        if not url:
            url = settings.MAILERLITE_API_SUBSCRIBERS_URL

        payload = {
            "email": email_address.email,
            "resubscribe": True,
        }
        headers = {
            "X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY,
        }
        try:
            # TODO: migrate this signal to a Celery task since it has a `requests.post` on it.
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=3,  # seconds
            )
            resp.raise_for_status()
        except requests.Timeout:
            log.warning("Timeout subscribing user to newsletter.")
        except Exception:  # noqa
            log.exception("Unknown error subscribing user to newsletter.")


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
            version_slug = unresolved.version.slug
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
