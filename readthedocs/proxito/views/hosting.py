"""Views for hosting features."""

import structlog
from django.conf import settings
from django.http import JsonResponse
from django.views import View

from readthedocs.core.mixins import CDNCacheControlMixin

log = structlog.get_logger(__name__)  # noqa


class ReadTheDocsConfigJson(CDNCacheControlMixin, View):
    def get(self, request):

        unresolved_domain = request.unresolved_domain
        project = unresolved_domain.project

        # TODO: use Referrer header or GET arguments for Version / Build
        version_slug = project.get_default_version()
        version = project.versions.get(slug=version_slug)
        build = version.builds.last()

        # TODO: define how it will be the exact JSON object returned here
        data = {
            "project": {
                "slug": project.slug,
            },
            "version": {
                "slug": version.slug,
            },
            "build": {
                "id": build.pk,
            },
            "domains": {
                "dashboard": settings.PRODUCTION_DOMAIN,
            },
        }

        return JsonResponse(data, json_dumps_params=dict(indent=4))
