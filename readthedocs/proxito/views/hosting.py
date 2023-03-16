"""Views for hosting features."""

import structlog
from django.conf import settings
from django.http import JsonResponse
from django.views import View

from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.resolver import resolver
from readthedocs.core.unresolver import unresolver

log = structlog.get_logger(__name__)  # noqa


class ReadTheDocsConfigJson(CDNCacheControlMixin, View):
    def get(self, request):

        url = request.GET.get("url")
        if not url:
            return JsonResponse(
                {"error": "'url' GET attribute is required"},
                status=400,
            )

        unresolved_domain = request.unresolved_domain
        project = unresolved_domain.project

        # TODO: why the UnresolvedURL object is not injected in the `request` by the middleware.
        # Is is fine to calculate it here?
        unresolved_url = unresolver.unresolve_url(url)
        version = unresolved_url.version

        # TODO: use Referrer header or GET arguments for Version / Build
        project.get_default_version()
        build = version.builds.last()

        # TODO: define how it will be the exact JSON object returned here
        # NOTE: we could use the APIv3 serializers for some of these objects
        # if we want to keep consistency. However, those may require some
        # extra db calls that we probably want to avoid.
        data = {
            "comment": (
                "THIS RESPONSE IS IN ALPHA FOR TEST PURPOSES ONLY"
                " AND IT'S GOING TO CHANGE COMPLETELY -- DO NOT USE IT!"
            ),
            "project": {
                "slug": project.slug,
                "language": project.language,
                "repository_url": project.repo,
                "programming_language": project.programming_language,
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
            "readthedocs": {
                "analytics": {
                    "code": settings.GLOBAL_ANALYTICS_CODE,
                },
            },
            "features": {
                "analytics": {
                    "code": project.analytics_code,
                },
                "external_version_warning": {
                    "enabled": True,
                    "query_selector": "[role=main]",
                },
                "non_latest_version_warning": {
                    "enabled": True,
                    "query_selector": "[role=main]",
                    "versions": list(
                        project.versions.filter(active=True)
                        .only("slug")
                        .values_list("slug", flat=True)
                    ),
                },
                "doc_diff": {
                    "enabled": True,
                    # "http://test-builds-local.devthedocs.org/en/latest/index.html"
                    "base_url": f"""{resolver.resolve(
                        project=project,
                        version_slug=project.get_default_version(),
                        language=project.language,
                        filename=unresolved_url.filename,
                    )}""",
                    "root_selector": "[role=main]",
                    "inject_styles": True,
                    # NOTE: `base_host` and `base_page` are not required, since
                    # we are constructing the `base_url` in the backend instead
                    # of the frontend, as the doc-diff extension does.
                    "base_host": "",
                    "base_page": "",
                },
                "flyout": {
                    "translations": [],
                    "versions": [
                        {
                            "slug": version.slug,
                            "url": f"/{project.language}/{version.slug}/",
                        }
                        for version in project.versions.filter(active=True).only("slug")
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
