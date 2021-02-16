import logging

log = logging.getLogger(__name__)


class CachedResponseMixin:

    """
    Add cache tags for project and version to the response of this view.

    The view inheriting this mixin should implement the
    `self._get_project` and `self._get_version` methods.
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        cache_tags = self._get_cache_tags()
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
            return [
                project.slug,
                f'{project.slug}-{version.slug}',
            ]
        except Exception as e:
            log.debug('Error while retrieving project and version for this view.')
        return []
