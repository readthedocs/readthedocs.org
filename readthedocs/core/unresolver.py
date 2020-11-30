import logging
from collections import namedtuple
from urllib.parse import urlparse

from django.test.client import RequestFactory
from django.urls import resolve as url_resolve

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.proxito.middleware import map_host_to_project_slug
from readthedocs.proxito.views.mixins import ServeDocsMixin
from readthedocs.proxito.views.utils import _get_project_data_from_request

log = logging.getLogger(__name__)

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

        log.info(
            'Unresolver parsed: '
            'project=%s lang_slug=%s version_slug=%s filename=%s',
            final_project.slug, lang_slug, version_slug, filename
        )
        return UnresolvedObject(final_project, lang_slug, version_slug, filename, parsed.fragment)


class Unresolver(SettingsOverrideObject):

    _default_class = UnresolverBase


unresolver = Unresolver()
unresolve = unresolver.unresolve
unresolve_from_request = unresolver.unresolve_from_request
