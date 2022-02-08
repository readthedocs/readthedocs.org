import structlog
from django.conf import settings

from readthedocs.projects.models import Feature

log = structlog.get_logger(__name__)


class CachedResponseMixin:

    """
    Add cache tags for project and version to the response of this view.

    The view inheriting this mixin should implement the
    `self._get_project` and `self._get_version` methods.

    You can add an extra per-project tag by overriding the `project_cache_tag` attribute.
    """

    project_cache_tag = None
    set_cache_control_header = False

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        cache_tags = self._get_cache_tags()
        if cache_tags:
            response.headers['Cache-Tag'] = ','.join(cache_tags)

        if self.set_cache_control_header:
            cache_control = self._get_cache_control_header()
            if cache_control:
                response.headers['CDN-Cache-Control'] = cache_control

        return response

    def _get_cache_control_header(self):
        """
        Get the value for the CDN-Cache-Control header.

        If privacy levels aren't enabled
        we don't set the header, as everything is public.

        If privacy levels are enabled,
        we cache the response if the version
        attached to the request is public.
        """
        if not settings.ALLOW_PRIVATE_REPOS:
            return None

        try:
            project = self._get_project()
            version = self._get_version()
        except Exception:
            log.debug('Error while retrieving project and/or version for this view.')
            return None

        if (
            project
            and project.has_feature(Feature.CDN_ENABLED)
            and version
            and not version.is_private
        ):
            return 'public'
        return None

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
