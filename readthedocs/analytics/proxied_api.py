"""Analytics views that are served from the same domain as the docs."""
from functools import lru_cache
from urllib.parse import urlparse

import structlog
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.analytics.models import PageView
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.unresolver import UnresolverError, unresolve
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.core.utils.requests import is_suspicious_request
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)  # noqa

class BaseAnalyticsView(CDNCacheControlMixin, APIView):

    """
    Track page views.

    Query parameters:

    - project
    - version
    - absolute_uri: Full path with domain.
    """

    # We always want to hit our analytics endpoint,
    # so we capture all views/interactions.
    cache_response = False
    http_method_names = ["get"]
    permission_classes = [IsAuthorizedToViewVersion]

    @lru_cache(maxsize=1)
    def _get_project(self):
        project_slug = self.request.GET.get("project")
        project = get_object_or_404(Project, slug=project_slug)
        return project

    @lru_cache(maxsize=1)
    def _get_version(self):
        version_slug = self.request.GET.get("version")
        project = self._get_project()
        version = get_object_or_404(
            project.versions.all(),
            slug=version_slug,
        )
        return version

    def get(self, request, *args, **kwargs):
        # TODO: Use absolute_uri only, we don't need project and version.
        project = self._get_project()
        version = self._get_version()
        absolute_uri = self.request.GET.get("absolute_uri")
        if not absolute_uri:
            return JsonResponse(
                {"error": "'absolute_uri' GET attribute is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.increase_page_view_count(
            project=project,
            version=version,
            absolute_uri=absolute_uri,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def increase_page_view_count(self, project, version, absolute_uri):
        """Increase the page view count for the given project."""
        if is_suspicious_request(self.request):
            log.info(
                "Suspicious request, not recording pageview.",
                url=absolute_uri,
            )
            return

        # Don't allow tracking page views from external domains.
        if self.request.unresolved_domain.is_from_external_domain:
            return

        try:
            unresolved = unresolve(absolute_uri)
        except UnresolverError:
            # If we were unable to resolve the URL, it
            # isn't pointing to a valid RTD project.
            return

        # Don't track external versions.
        if version.is_external or not unresolved.filename:
            return

        path = urlparse(absolute_uri).path
        PageView.objects.register_page_view(
            project=project,
            version=version,
            filename=unresolved.filename,
            path=path,
            status=200,
        )


class AnalyticsView(SettingsOverrideObject):
    _default_class = BaseAnalyticsView
