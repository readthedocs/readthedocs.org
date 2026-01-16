import functools

import structlog
from django.http import Http404
from django.utils.functional import cached_property

from readthedocs.core.unresolver import UnresolverError
from readthedocs.core.unresolver import unresolve
from readthedocs.core.utils import get_cache_tag
from readthedocs.proxito.cache import add_cache_tags


log = structlog.get_logger(__name__)


class CDNCacheTagsMixin:
    """
    Add cache tags for project and version to the response of this view.

    The view inheriting this mixin can either call :py:method:`set_cache_tags` or
    implement the ``self._get_project`` and ``self._get_version`` methods.

    You can add an extra per-project tag by overriding the `project_cache_tag` attribute.
    """

    project_cache_tag = None

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        cache_tags = getattr(self, "_cache_tags", self._get_cache_tags())
        if cache_tags:
            add_cache_tags(response, cache_tags)
        return response

    def _get_cache_tags(self, project=None, version=None):
        """
        Get cache tags for this view.

        This returns an array of tag identifiers used to tag the response at CDN.

        If project and version are not passed in, these values will come from the
        methods ``_get_project()`` and ``_get_version()``.
        If ``_get_version()`` returns ``None``, only the project level tags are added.

        It's easier to use :py:method:`set_cache_tags` if project/version aren't
        set at the instance level, or if they are passed in through a method
        like ``get()``.

        .. warning::

           This method is run at the end of the request,
           so any exceptions like 404 should be caught.
        """
        if project is None and version is None:
            try:
                project = self._get_project()
                version = self._get_version()
            except Exception:
                log.warning(
                    "Error while retrieving project or version for this view.",
                    exc_info=True,
                )
                return []

        tags = []
        if project:
            tags.append(project.slug)
        if project and version:
            tags.append(get_cache_tag(project.slug, version.slug))
        if project and self.project_cache_tag:
            tags.append(get_cache_tag(project.slug, self.project_cache_tag))
        return tags

    def set_cache_tags(self, project=None, version=None):
        """
        Store cache tags to be added to response.

        This method can be used if project/version do not exist on the view
        instance or if they are passed into the view through a method like
        ``get()``.

        The attribute methods ``_get_project()``/``_get_version()`` aren`t used
        in this pattern.
        """
        self._cache_tags = self._get_cache_tags(project, version)


class EmbedAPIMixin:
    """
    Helper for EmbedAPI v2 and v3.

    Used in combination with ``CDNCacheTagsMixin`` to add project/version slug
    in the response to be cached.

    Note that these methods are cached (``lru_cache`` and ``cached_property``)
    to avoid hitting the database multiple times on the same request.
    """

    @cached_property
    def unresolved_url(self):
        url = self.request.GET.get("url")
        if not url:
            return None
        try:
            return unresolve(url)
        except UnresolverError:
            # If we were unable to resolve the URL, it
            # isn't pointing to a valid RTD project.
            return None

    @functools.lru_cache(maxsize=1)
    def _get_project(self):
        if self.external:
            return None

        if self.unresolved_url:
            return self.unresolved_url.project

        raise Http404

    @functools.lru_cache(maxsize=1)
    def _get_version(self):
        if self.external:
            return None

        if self.unresolved_url:
            return self.unresolved_url.version

        raise Http404
