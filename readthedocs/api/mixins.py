import functools

import structlog
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from readthedocs.core.unresolver import unresolve
from readthedocs.core.utils import get_cache_tag
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)


class CDNCacheTagsMixin:

    """
    Add cache tags for project and version to the response of this view.

    The view inheriting this mixin should implement the
    `self._get_project` and `self._get_version` methods.

    If `self._get_version` returns `None`,
    only the project level tags are added.

    You can add an extra per-project tag by overriding the `project_cache_tag` attribute.
    """

    project_cache_tag = None

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        cache_tags = self._get_cache_tags()
        if cache_tags:
            response["Cache-Tag"] = ",".join(cache_tags)
        return response

    def _get_cache_tags(self):
        """
        Get cache tags for this view.

        .. warning::

           This method is run at the end of the request,
           so any exceptions like 404 should be caught.
        """
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
        return unresolve(url)

    @functools.lru_cache(maxsize=1)
    def _get_project(self):
        if self.external:
            return

        if self.unresolved_url:
            project_slug = self.unresolved_url.project.slug
        else:
            project_slug = self.request.GET.get("project")
        return get_object_or_404(Project, slug=project_slug)

    @functools.lru_cache(maxsize=1)
    def _get_version(self):
        if self.external:
            return

        if self.unresolved_url:
            version_slug = self.unresolved_url.version.slug
        else:
            version_slug = self.request.GET.get("version", "latest")
        project = self._get_project()
        return get_object_or_404(project.versions.all(), slug=version_slug)
