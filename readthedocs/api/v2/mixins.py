import logging

log = logging.getLogger(__name__)


class CachedResponseMixin:

    """
    Add cache tags for project and version to the response of this view.

    The view inheriting this mixin should implement the
    `self._get_project` and `self._get_version` methods.

    You can add an extra per-project tag by overriding the `project_cache_tag` attribute.
    """

    project_cache_tag = None

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        cache_tags = self._get_cache_tags()
        if cache_tags:
            response['Cache-Tag'] = ','.join(cache_tags)
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
            tags = [
                project.slug,
                f'{project.slug}-{version.slug}',
            ]
            if self.project_cache_tag:
                tags.append(f'{project.slug}-{self.project_cache_tag}')
            return tags
        except Exception as e:
            log.debug('Error while retrieving project and version for this view.')
        return []
