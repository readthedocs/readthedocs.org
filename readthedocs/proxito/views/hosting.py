"""Views for hosting features."""

import packaging
import structlog
from django.conf import settings
from django.http import JsonResponse
from django.views import View

from readthedocs.api.v3.serializers import (
    BuildSerializer,
    ProjectSerializer,
    VersionSerializer,
)
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.resolver import resolver
from readthedocs.core.unresolver import unresolver

log = structlog.get_logger(__name__)  # noqa


ADDONS_VERSIONS_SUPPORTED = (0, 1)


class ClientError(Exception):
    VERSION_NOT_CURRENTLY_SUPPORTED = (
        "The version specified in 'X-RTD-Hosting-Integrations-Version'"
        " is currently not supported"
    )
    VERSION_INVALID = "'X-RTD-Hosting-Integrations-Version' header version is invalid"
    VERSION_HEADER_MISSING = (
        "'X-RTD-Hosting-Integrations-Version' header attribute is required"
    )


class ReadTheDocsConfigJson(CDNCacheControlMixin, View):

    """
    API response consumed by our JavaScript client.

    The code for the JavaScript client lives at:
      https://github.com/readthedocs/readthedocs-client/

    Attributes:

      url (required): absolute URL from where the request is performed
        (e.g. ``window.location.href``)
    """

    def get(self, request):

        url = request.GET.get("url")
        if not url:
            return JsonResponse(
                {"error": "'url' GET attribute is required"},
                status=400,
            )

        addons_version = request.headers.get("X-RTD-Hosting-Integrations-Version")
        if not addons_version:
            return JsonResponse(
                {
                    "error": ClientError.VERSION_HEADER_MISSING,
                },
                status=400,
            )
        try:
            addons_version = packaging.version.parse(addons_version)
            if addons_version.major not in ADDONS_VERSIONS_SUPPORTED:
                raise ClientError
        except packaging.version.InvalidVersion:
            return JsonResponse(
                {
                    "error": ClientError.VERSION_INVALID,
                },
                status=400,
            )
        except ClientError:
            return JsonResponse(
                {"error": ClientError.VERSION_NOT_CURRENTLY_SUPPORTED},
                status=400,
            )

        unresolved_domain = request.unresolved_domain
        project = unresolved_domain.project

        unresolved_url = unresolver.unresolve_url(url)
        version = unresolved_url.version
        filename = unresolved_url.filename

        project.get_default_version()
        build = version.builds.last()

        data = AddonsResponse().get(addons_version, project, version, build, filename)
        return JsonResponse(data, json_dumps_params=dict(indent=4))


class NoLinksMixin:

    """Mixin to remove conflicting fields from serializers."""

    FIELDS_TO_REMOVE = (
        "_links",
        "urls",
    )

    def __init__(self, *args, **kwargs):
        super(NoLinksMixin, self).__init__(*args, **kwargs)

        for field in self.FIELDS_TO_REMOVE:
            if field in self.fields:
                del self.fields[field]

            if field in self.Meta.fields:
                del self.Meta.fields[self.Meta.fields.index(field)]


# NOTE: the following serializers are required only to remove some fields we
# can't expose yet in this API endpoint because it running under El Proxito
# which cannot resolve some dashboard URLs because they are not defined on El
# Proxito.
#
# See https://github.com/readthedocs/readthedocs-ops/issues/1323
class ProjectSerializerNoLinks(NoLinksMixin, ProjectSerializer):
    pass


class VersionSerializerNoLinks(NoLinksMixin, VersionSerializer):
    pass


class BuildSerializerNoLinks(NoLinksMixin, BuildSerializer):
    pass


class AddonsResponse:
    def get(self, addons_version, project, version, build, filename):
        """
        Unique entry point to get the proper API response.

        It will evaluate the ``addons_version`` passed and decide which is the
        best JSON structure for that particular version.
        """
        if addons_version.major == 0:
            return self._v0(project, version, build, filename)

        if addons_version.major == 1:
            return self._v1(project, version, build, filename)

    def _v0(self, project, version, build, filename):
        """
        Initial JSON data structure consumed by the JavaScript client.

        This response is definitely in *alpha* state currently and shouldn't be
        used for anyone to customize their documentation or the integration
        with the Read the Docs JavaScript client. It's under active development
        and anything can change without notice.

        It tries to follow some similarity with the APIv3 for already-known resources
        (Project, Version, Build, etc).
        """

        data = {
            "comment": (
                "THIS RESPONSE IS IN ALPHA FOR TEST PURPOSES ONLY"
                " AND IT'S GOING TO CHANGE COMPLETELY -- DO NOT USE IT!"
            ),
            "projects": {
                "current": ProjectSerializerNoLinks(project).data,
            },
            "versions": {
                "current": VersionSerializerNoLinks(version).data,
            },
            "builds": {
                "current": BuildSerializerNoLinks(build).data,
            },
            # TODO: consider creating one serializer per field here.
            # The resulting JSON will be the same, but maybe it's easier/cleaner?
            "domains": {
                "dashboard": settings.PRODUCTION_DOMAIN,
            },
            "readthedocs": {
                "analytics": {
                    "code": settings.GLOBAL_ANALYTICS_CODE,
                },
            },
            # TODO: the ``features`` is not polished and we expect to change drastically.
            # Mainly, all the fields including a Project, Version or Build will use the exact same
            # serializer than the keys ``project``, ``version`` and ``build`` from the top level.
            "addons": {
                "analytics": {
                    "enabled": True,
                    # TODO: consider adding this field into the ProjectSerializer itself.
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
                    "base_url": resolver.resolve(
                        project=project,
                        version_slug=project.get_default_version(),
                        language=project.language,
                        filename=filename,
                    ),
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
                "search": {
                    "enabled": True,
                    "project": project.slug,
                    "version": version.slug,
                    "api_endpoint": "/_/api/v3/search/",
                    # TODO: figure it out where this data comes from
                    "filters": [
                        [
                            "Search only in this project",
                            f"project:{project.slug}/{version.slug}",
                        ],
                        [
                            "Search subprojects",
                            f"subprojects:{project.slug}/{version.slug}",
                        ],
                    ],
                    "default_filter": f"subprojects:{project.slug}/{version.slug}",
                },
            },
        }

        # Update this data with the one generated at build time by the doctool
        if version.build_data:
            data.update(version.build_data)

        return data

    def _v1(self, project, version, build, filename):
        return {
            "comment": "Undefined yet. Use v0 for now",
        }
