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

    The view inheriting this mixin should implement the
    `self._get_project` and `self._get_version` methods.

    If `self._get_version` returns `None`,
    only the project level tags are added.

    You can add an extra per-project tag by overriding the `project_cache_tag` attribute.

    Views whose response involves several projects (like search)
    should override `self._get_projects_and_versions` instead,
    every pair gets the same set of tags.
    """

    project_cache_tag = None

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        cache_tags = self._get_cache_tags()
        if cache_tags:
            add_cache_tags(response, cache_tags)
        return response

    def _get_cache_tags(self):
        """
        Get cache tags for this view.

        .. warning::

           This method is run at the end of the request,
           so any exceptions like 404 should be caught.
        """
        try:
            projects_and_versions = self._get_projects_and_versions()
        except Exception:
            log.warning(
                "Error while retrieving project or version for this view.",
                exc_info=True,
            )
            return []

        tags = []
        for project, version in projects_and_versions:
            if not project:
                continue
            tags.append(project.slug)
            if version:
                tags.append(get_cache_tag(project.slug, version.slug))
            if self.project_cache_tag:
                tags.append(get_cache_tag(project.slug, self.project_cache_tag))
        # The same project can appear more than once with different versions.
        return list(dict.fromkeys(tags))

    def _get_projects_and_versions(self):
        """Return the list of ``(project, version)`` pairs to tag the response with."""
        return [(self._get_project(), self._get_version())]


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
