"""Analytics views that are served from the same domain as the docs."""

from functools import lru_cache
from urllib.parse import urlparse

import structlog
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status as status_codes
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.analytics.models import PageView
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.unresolver import InvalidPathForVersionedProjectError
from readthedocs.core.unresolver import UnresolverError
from readthedocs.core.unresolver import unresolver
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.core.utils.requests import is_suspicious_request
from readthedocs.projects.models import Project
from readthedocs.proxito.views.hosting import IsAuthorizedToViewProject


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
    permission_classes = [IsAuthorizedToViewProject | IsAuthorizedToViewVersion]

    @lru_cache(maxsize=1)
    def _get_project(self):
        project_slug = self.request.GET.get("project")
        project = get_object_or_404(Project, slug=project_slug)
        return project

    @lru_cache(maxsize=1)
    def _get_version(self):
        version_slug = self.request.GET.get("version")
        project = self._get_project()
        # Do not call `get_object_or_404` because there may be some invalid URLs without versions.
        # We do want to track those 404 pages as well. In that case, the `filename` attribute is the `path`.
        version = project.versions.filter(slug=version_slug).first()
        return version

    def get(self, request, *args, **kwargs):
        # TODO: Use absolute_uri only, we don't need project and version.
        project = self._get_project()
        version = self._get_version()
        absolute_uri = self.request.GET.get("absolute_uri")
        status = self.request.GET.get("status", "200")
        if not absolute_uri:
            return JsonResponse(
                {"error": "'absolute_uri' GET attribute is required"},
                status=status_codes.HTTP_400_BAD_REQUEST,
            )

        if status not in ("200", "404"):
            return JsonResponse(
                {"error": "'status' GET attribute should be 200 or 404"},
                status=status_codes.HTTP_400_BAD_REQUEST,
            )

        self.increase_page_view_count(
            project=project,
            version=version,
            absolute_uri=absolute_uri,
            status=status,
        )
        return Response(status=status_codes.HTTP_204_NO_CONTENT)

    def increase_page_view_count(self, project, version, absolute_uri, status):
        """Increase the page view count for the given project."""
        if is_suspicious_request(self.request):
            log.info(
                "Suspicious request, not recording pageview.",
                url=absolute_uri,
            )
            return

        # Don't track 200 if the version doesn't exist
        if status == "200" and not version:
            return

        # Don't allow tracking page views from external domains.
        if self.request.unresolved_domain.is_from_external_domain:
            return

        # Don't track external versions.
        if version and version.is_external:
            return

        try:
            absolute_uri_parsed = urlparse(absolute_uri)
        except ValueError as e:
            log.info(
                "Skipping page view count due to URL parsing error",
                url=absolute_uri,
                error=str(e),
            )
            return

        try:
            unresolved = unresolver.unresolve_url(absolute_uri)
            filename = unresolved.filename
            absolute_uri_project = unresolved.project
        except InvalidPathForVersionedProjectError as exc:
            # If the version is missing, we still want to log this request.
            #
            # If we don't have a version, the filename is the path,
            # otherwise it would be empty.
            filename = exc.path
            absolute_uri_project = exc.project
        except UnresolverError:
            # If we were unable to resolve the URL, it
            # isn't pointing to a valid RTD project.
            return

        if absolute_uri_project.slug != project.slug:
            log.warning(
                "Skipping page view count since projects don't match",
                project_slug=project.slug,
                uri_project_slug=absolute_uri_project.slug,
            )
            return

        PageView.objects.register_page_view(
            project=project,
            version=version,
            filename=filename,
            path=absolute_uri_parsed.path,
            status=status,
        )


class AnalyticsView(SettingsOverrideObject):
    _default_class = BaseAnalyticsView
