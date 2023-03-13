"""Views for hosting features."""

import structlog
from django.conf import settings
from django.http import JsonResponse
from django.views import View

from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.unresolver import unresolver

log = structlog.get_logger(__name__)  # noqa


class ReadTheDocsConfigJson(CDNCacheControlMixin, View):
    def get(self, request):

        unresolved_domain = request.unresolved_domain
        project = unresolved_domain.project

        # TODO: why the UnresolvedURL object is not injected in the `request` by the middleware.
        # Is is fine to calculate it here?
        unresolved_url = unresolver.unresolve_url(request.headers.get("Referer"))
        version = unresolved_url.version

        # TODO: use Referrer header or GET arguments for Version / Build
        project.get_default_version()
        build = version.builds.last()

        # TODO: define how it will be the exact JSON object returned here
        data = {
            "project": {
                "slug": project.slug,
                "language": project.language,
                "repository_url": project.repo,
            },
            "version": {
                "slug": version.slug,
                "external": version.type == EXTERNAL,
            },
            "build": {
                "id": build.pk,
            },
            "domains": {
                "dashboard": settings.PRODUCTION_DOMAIN,
            },
            "features": {
                "external_version_warning": {
                    "enabled": True,
                    "query_selector": "[role=main]",
                },
                "non_latest_version_warning": {
                    "enabled": True,
                    "query_selector": "[role=main]",
                    "versions": list(
                        project.versions.filter(active=True).values_list(
                            "slug", flat=True
                        )
                    ),
                },
                "doc_diff": True,
                "flyout": {
                    "translations": [],
                    "versions": [
                        {
                            "slug": version.slug,
                            "url": f"/{project.language}/{version.slug}/",
                        }
                        for version in project.versions.filter(active=True)
                    ],
                    "downloads": [],
                    # TODO: get this values properly
                    "vcs": {
                        "url": "https://github.com",
                        "username": "readthedocs",
                        "repository": "test-builds",
                        "branch": version.identifier,
                        "filepath": "/docs/index.rst",
                    },
                },
            },
        }

        # Update this data with the one generated at build time by the doctool
        if version.build_data:
            data.update(version.build_data)

        return JsonResponse(data, json_dumps_params=dict(indent=4))
