import structlog

from readthedocs.core.utils import get_cache_tag

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
