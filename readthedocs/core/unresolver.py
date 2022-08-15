import structlog
from django.conf import settings
from collections import namedtuple
from urllib.parse import urlparse

from django.test.client import RequestFactory
from django.urls import resolve as url_resolve

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.proxito.middleware import map_host_to_project_slug
from readthedocs.proxito.views.mixins import ServeDocsMixin
from readthedocs.projects.models import Domain
from readthedocs.proxito.views.utils import _get_project_data_from_request

log = structlog.get_logger(__name__)

UnresolvedObject = namedtuple(
    'Unresolved', 'project, language_slug, version_slug, filename, fragment')


class UnresolverBase:

    def unresolve(self, url):
        """
        Turn a URL into the component parts that our views would use to process them.

        This is useful for lots of places,
        like where we want to figure out exactly what file a URL maps to.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.split(':', 1)[0]

        # TODO: Make this not depend on the request object,
        # but instead move all this logic here working on strings.
        request = RequestFactory().get(path=parsed.path, HTTP_HOST=domain)
        project_slug = map_host_to_project_slug(request)

        # Handle returning a response
        if hasattr(project_slug, 'status_code'):
            return None

        request.host_project_slug = request.slug = project_slug
        return self.unresolve_from_request(request, url)

    def unresolve_from_request(self, request, path):
        """
        Unresolve using a request.

        ``path`` can be a full URL, but the domain will be ignored,
        since that information is already in the request object.

        None is returned if the request isn't valid.
        """
        parsed = urlparse(path)
        path = parsed.path
        project_slug = getattr(request, 'host_project_slug', None)

        if not project_slug:
            return None

        _, __, kwargs = url_resolve(
            path,
            urlconf='readthedocs.proxito.urls',
        )

        mixin = ServeDocsMixin()
        version_slug = mixin.get_version_from_host(request, kwargs.get('version_slug'))

        final_project, lang_slug, version_slug, filename = _get_project_data_from_request(  # noqa
            request,
            project_slug=project_slug,
            subproject_slug=kwargs.get('subproject_slug'),
            lang_slug=kwargs.get('lang_slug'),
            version_slug=version_slug,
            filename=kwargs.get('filename', ''),
        )

        # Handle our backend storage not supporting directory indexes,
        # so we need to append index.html when appropriate.
        if not filename or filename.endswith('/'):
            # We need to add the index.html to find this actual file
            filename += 'index.html'

        log.debug(
            'Unresolver parsed.',
            project_slug=final_project.slug,
            lang_slug=lang_slug,
            version_slug=version_slug,
            filename=filename,
        )
        return UnresolvedObject(final_project, lang_slug, version_slug, filename, parsed.fragment)

    @staticmethod
    def get_domain_from_host(host):
        """
        Get the normalized domain from a hostname.

        A hostname can include the port.
        """
        return host.lower().split(":")[0]

    # TODO: make this a private method once
    # proxito uses the unresolve method directly.
    def unresolve_domain(self, domain):
        """
        Unresolve domain by extracting relevant information from it.

        :param str domain: Domain to extract the information from.
        :returns: A tuple with: the project slug, domain object, and if the domain
        is from an external version.
        """
        public_domain = self.get_domain_from_host(settings.PUBLIC_DOMAIN)
        external_domain = self.get_domain_from_host(settings.RTD_EXTERNAL_VERSION_DOMAIN)

        subdomain, *rest_of_domain = domain.split(".", maxsplit=1)
        rest_of_domain = rest_of_domain[0] if rest_of_domain else ""

        if public_domain in domain:
            # Serve from the PUBLIC_DOMAIN, ensuring it looks like `foo.PUBLIC_DOMAIN`.
            if public_domain == rest_of_domain:
                project_slug = subdomain
                return project_slug, None, False

            # TODO: This can catch some possibly valid domains (docs.readthedocs.io.com) for example,
            # but these might be phishing, so let's ignore them for now.
            return None, None, False

        if external_domain in domain:
            # Serve custom versions on external-host-domain.
            if external_domain == rest_of_domain:
                try:
                    project_slug, _ = subdomain.rsplit("--", maxsplit=1)
                    return project_slug, None, True
                except ValueError:
                    return None, None, False

        # Custom domain.
        domain_object = (
            Domain.objects.filter(domain=domain).prefetch_related("project").first()
        )
        if domain_object:
            project_slug = domain_object.project.slug
            return project_slug, domain_object, False

        return None, None, None


class Unresolver(SettingsOverrideObject):

    _default_class = UnresolverBase


unresolver = Unresolver()
unresolve = unresolver.unresolve
unresolve_from_request = unresolver.unresolve_from_request
