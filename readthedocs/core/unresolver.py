import logging
from urllib.parse import urlparse
from collections import namedtuple

from django.urls import resolve as url_resolve
from django.test.client import RequestFactory

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.proxito.middleware import map_host_to_project_slug
from readthedocs.proxito.views.utils import _get_project_data_from_request
from readthedocs.proxito.views.mixins import ServeDocsMixin

log = logging.getLogger(__name__)

UnresolvedObject = namedtuple(
    'Unresolved', 'project, language_slug, version_slug, filename, fragment')


class UnresolverBase:

    def unresolve(self, uri):
        """
        Turn a URL into the component parts that our views would use to process them.

        This is useful for lots of places,
        like where we want to figure out exactly what file a URL maps to.
        """
        parsed = urlparse(uri)
        domain = parsed.netloc.split(':', 1)[0]
        path = parsed.path

        # TODO: Make this not depend on the request object,
        # but instead move all this logic here working on strings.
        request = RequestFactory().get(path=path, HTTP_HOST=domain)
        project_slug = request.host_project_slug = map_host_to_project_slug(request)

        # Handle returning a response
        if hasattr(project_slug, 'status_code'):
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

        log.info('Unresolved: %s', locals())
        return UnresolvedObject(final_project, lang_slug, version_slug, filename, parsed.fragment)


class Unresolver(SettingsOverrideObject):

    _default_class = UnresolverBase


unresolver = Unresolver()
unresolve = unresolver.unresolve
