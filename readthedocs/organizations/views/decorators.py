import functools

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import NoReverseMatch
from django.utils.http import urlencode
from structlog import get_logger

from readthedocs.organizations.models import Organization

log = get_logger(__name__)


def redirect_if_organization_unspecified(dispatch):
    """
    It is possible to share a URL to an organization page without specifying the organization slug.

    This decorates the dispatch() method of Class Based Views operating on the Organization model.

    In case the slug is specified as "-", we do the following:

    1. Check if there is only 1 organization available and redirect to this one
    2. Redirect to an "organization chooser", where the user will pick from a list of organizations.
    """

    @functools.wraps(dispatch)
    def inner(cbv_object, *args, **kwargs):
        slug = cbv_object.kwargs.get("slug", "")

        # Magic '-' slug means that an organization hasn't been set in the URL.
        if slug == "-":

            organizations = Organization.objects.for_user(user=cbv_object.request.user)

            current_url_name = cbv_object.request.resolver_match.url_name
            current_url_kwargs = cbv_object.request.resolver_match.kwargs
            current_url_args = cbv_object.request.resolver_match.args

            # This type of redirect is pretty meaningless for views with arguments
            # because the kwargs are almost always dependent on the organization slug
            # (teams, members etc)
            if current_url_args or not all(
                k == "slug" for k in current_url_kwargs.keys()
            ):
                log.warning(
                    "Tried to use unspecific 'slug' argument for a url with addition arguments",
                    kwargs=current_url_kwargs,
                    args=current_url_args,
                )
                raise Http404

            querystring = cbv_object.request.META.get("QUERY_STRING", None)

            # User is a member of exactly 1 organization, so we can redirect here.
            if organizations.count() == 1:
                try:
                    destination_url = resolve_url(
                        current_url_name, slug=organizations.first().slug
                    )
                except NoReverseMatch:
                    log.warning(
                        "Tried to redirect from unspecified slug to a URL name that doesn't exist"
                    )
                    raise Http404
                if querystring:
                    destination_url += "?" + querystring
                return HttpResponseRedirect(destination_url)

            # User is a member of 0 or >1 organizations: redirect to the chooser page
            destination_url = resolve_url(
                "organization_choose",
                next_name=current_url_name,
            )

            if querystring:
                destination_url += "?next_querystring=" + urlencode(querystring)
            return HttpResponseRedirect(destination_url)

        # Continue the call
        return dispatch(cbv_object, *args, **kwargs)

    return inner


def redirect_if_organizations_disabled(dispatch):
    """
    Return 404 if organizations aren't enabled.

    All organization views should decorate their view functions with this.

    The reason for implementing it this way is that
    the organization urls cannot be added conditionally on readthedocs/urls.py,
    as the file is evaluated only once, not per-test case.
    """

    @functools.wraps(dispatch)
    def inner(*args, **kwargs):
        if not settings.RTD_ALLOW_ORGANIZATIONS:
            raise Http404
        return dispatch(*args, **kwargs)

    return inner
