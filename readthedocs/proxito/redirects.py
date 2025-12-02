from urllib.parse import urlparse

import structlog
from django.http import HttpResponseRedirect

from readthedocs.core.resolver import Resolver
from readthedocs.core.utils.url import unsafe_join_url_path
from readthedocs.proxito.cache import cache_response
from readthedocs.proxito.constants import RedirectType
from readthedocs.redirects.exceptions import InfiniteRedirectException


log = structlog.get_logger(__name__)


def redirect_to_https(request, project):
    """
    Shortcut to get a https redirect.

    :param request: Request object.
    :param project: The current project being served
    """
    return canonical_redirect(request, project, RedirectType.http_to_https)


def canonical_redirect(request, project, redirect_type, external_version_slug=None):
    """
    Return a canonical redirect response.

    All redirects are cached, since the final URL will be checked for authorization.

    The following cases are covered:

    - Redirect a custom domain from http to https
        http://project.rtd.io/ -> https://project.rtd.io/
    - Redirect a domain to a canonical domain (http or https).
        http://project.rtd.io/ -> https://docs.test.com/
        http://project.rtd.io/foo/bar/ -> https://docs.test.com/foo/bar/
    - Redirect from a subproject domain to the main domain
        https://subproject.rtd.io/en/latest/foo -> https://main.rtd.io/projects/subproject/en/latest/foo  # noqa
        https://subproject.rtd.io/en/latest/foo -> https://docs.test.com/projects/subproject/en/latest/foo  # noqa

    Raises ``InfiniteRedirectException`` if the redirect is the same as the current URL.

    :param request: Request object.
    :param project: The current project being served
    :param redirect_type: The type of canonical redirect (https, canonical-cname, subproject-main-domain)
    :param external_version_slug: The version slug if the request is from a pull request preview.
    """
    from_url = request.build_absolute_uri()
    parsed_from = urlparse(from_url)

    if redirect_type == RedirectType.http_to_https:
        # We only need to change the protocol.
        to = parsed_from._replace(scheme="https").geturl()
    elif redirect_type == RedirectType.to_canonical_domain:
        # We need to change the domain and protocol.
        canonical_domain = project.canonical_custom_domain
        protocol = "https" if canonical_domain.https else "http"
        to = parsed_from._replace(scheme=protocol, netloc=canonical_domain.domain).geturl()
    elif redirect_type == RedirectType.subproject_to_main_domain:
        # We need to get the subproject root in the domain of the main
        # project, and append the current path.
        project_doc_prefix = Resolver().get_subproject_url_prefix(
            project=project,
            external_version_slug=external_version_slug,
        )
        parsed_doc_prefix = urlparse(project_doc_prefix)
        to = parsed_doc_prefix._replace(
            path=unsafe_join_url_path(parsed_doc_prefix.path, parsed_from.path),
            query=parsed_from.query,
        ).geturl()
    else:
        raise NotImplementedError

    if from_url == to:
        # check that we do have a response and avoid infinite redirect
        log.debug(
            "Infinite Redirect: FROM URL is the same than TO URL.",
            url=to,
        )
        raise InfiniteRedirectException()

    log.debug("Canonical Redirect.", host=request.get_host(), from_url=from_url, to_url=to)
    resp = HttpResponseRedirect(to)
    resp["X-RTD-Redirect"] = redirect_type.name
    cache_response(resp, cache_tags=[project.slug])
    return resp
