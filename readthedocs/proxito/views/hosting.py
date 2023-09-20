"""Views for hosting features."""

from functools import lru_cache

import packaging
import structlog
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404, JsonResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.api.v3.serializers import (
    BuildSerializer,
    ProjectSerializer,
    VersionSerializer,
)
from readthedocs.builds.models import Version
from readthedocs.core.resolver import resolver
from readthedocs.core.unresolver import UnresolverError, unresolver
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.models import Feature

log = structlog.get_logger(__name__)  # noqa


ADDONS_VERSIONS_SUPPORTED = (0, 1)


class ClientError(Exception):
    VERSION_NOT_CURRENTLY_SUPPORTED = (
        "The version specified in 'api-version' is currently not supported"
    )
    VERSION_INVALID = "The version specifified in 'api-version' is invalid"


class BaseReadTheDocsConfigJson(CDNCacheTagsMixin, APIView):

    """
    API response consumed by our JavaScript client.

    The code for the JavaScript client lives at:
      https://github.com/readthedocs/addons/

    Attributes:

      url (required): absolute URL from where the request is performed
        (e.g. ``window.location.href``)

      api-version (required): API JSON structure version (e.g. ``0``, ``1``, ``2``).
    """

    http_method_names = ["get"]
    permission_classes = [IsAuthorizedToViewVersion]
    renderer_classes = [JSONRenderer]
    project_cache_tag = "rtd-addons"

    @lru_cache(maxsize=1)
    def _resolve_resources(self):
        url = self.request.GET.get("url")
        if not url:
            # TODO: not sure what to return here when it fails on the `has_permission`
            return None, None, None, None

        unresolved_domain = self.request.unresolved_domain

        # Main project from the domain.
        project = unresolved_domain.project

        try:
            unresolved_url = unresolver.unresolve_url(url)
            # Project from the URL: if it's a subproject it will differ from
            # the main project got from the domain.
            project = unresolved_url.project
            version = unresolved_url.version
            filename = unresolved_url.filename
            build = version.builds.last()

        except UnresolverError as exc:
            # If an exception is raised and there is a ``project`` in the
            # exception, it's a partial match. This could be because of an
            # invalid URL path, but on a valid project domain. In this case, we
            # continue with the ``project``, but without a ``version``.
            # Otherwise, we return 404 NOT FOUND.
            project = getattr(exc, "project", None)
            if not project:
                raise Http404() from exc

            version = None
            filename = None
            build = None

        return project, version, build, filename

    def _get_project(self):
        project, version, build, filename = self._resolve_resources()
        return project

    def _get_version(self):
        project, version, build, filename = self._resolve_resources()
        return version

    def get(self, request, format=None):
        url = request.GET.get("url")
        if not url:
            return JsonResponse(
                {"error": "'url' GET attribute is required"},
                status=400,
            )

        addons_version = request.GET.get("api-version")
        if not addons_version:
            return JsonResponse(
                {"error": "'api-version' GET attribute is required"},
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

        project, version, build, filename = self._resolve_resources()

        data = AddonsResponse().get(
            addons_version,
            project,
            version,
            build,
            filename,
            user=request.user,
        )
        return JsonResponse(data, json_dumps_params={"indent": 4, "sort_keys": True})


class NoLinksMixin:

    """Mixin to remove conflicting fields from serializers."""

    FIELDS_TO_REMOVE = (
        "_links",
        "urls",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.FIELDS_TO_REMOVE:
            if field in self.fields:
                del self.fields[field]

            if field in self.Meta.fields:
                del self.Meta.fields[self.Meta.fields.index(field)]


# NOTE: the following serializers are required only to remove some fields we
# can't expose yet in this API endpoint because it's running under El Proxito
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
    def get(
        self,
        addons_version,
        project,
        version=None,
        build=None,
        filename=None,
        user=None,
    ):
        """
        Unique entry point to get the proper API response.

        It will evaluate the ``addons_version`` passed and decide which is the
        best JSON structure for that particular version.
        """
        if addons_version.major == 0:
            return self._v0(project, version, build, filename, user)

        if addons_version.major == 1:
            return self._v1(project, version, build, filename, user)

    def _v0(self, project, version, build, filename, user):
        """
        Initial JSON data structure consumed by the JavaScript client.

        This response is definitely in *alpha* state currently and shouldn't be
        used for anyone to customize their documentation or the integration
        with the Read the Docs JavaScript client. It's under active development
        and anything can change without notice.

        It tries to follow some similarity with the APIv3 for already-known resources
        (Project, Version, Build, etc).
        """
        version_downloads = []
        versions_active_built_not_hidden = Version.objects.none()

        if not project.single_version:
            versions_active_built_not_hidden = (
                Version.internal.public(
                    project=project,
                    only_active=True,
                    only_built=True,
                    user=user,
                )
                .exclude(hidden=True)
                .only("slug")
                .order_by("slug")
            )
            if version:
                version_downloads = version.get_downloads(pretty=True).items()

        project_translations = (
            project.translations.all().only("language").order_by("language")
        )
        # Make one DB query here and then check on Python code
        # TODO: make usage of ``Project.addons.<name>_enabled`` to decide if enabled
        project_features = project.features.all().values_list("feature_id", flat=True)

        data = {
            "api_version": "0",
            "comment": (
                "THIS RESPONSE IS IN ALPHA FOR TEST PURPOSES ONLY"
                " AND IT'S GOING TO CHANGE COMPLETELY -- DO NOT USE IT!"
            ),
            "projects": {
                # TODO: return the "parent" project here when the "current"
                # project is a subproject/translation.
                "current": ProjectSerializerNoLinks(project).data,
            },
            "versions": {
                "current": VersionSerializerNoLinks(version).data if version else None,
            },
            "builds": {
                "current": BuildSerializerNoLinks(build).data if build else None,
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
                    "enabled": Feature.ADDONS_ANALYTICS_DISABLED
                    not in project_features,
                    # TODO: consider adding this field into the ProjectSerializer itself.
                    # NOTE: it seems we are removing this feature,
                    # so we may not need the ``code`` attribute here
                    # https://github.com/readthedocs/readthedocs.org/issues/9530
                    "code": project.analytics_code,
                },
                "external_version_warning": {
                    "enabled": Feature.ADDONS_EXTERNAL_VERSION_WARNING_DISABLED
                    not in project_features,
                    # NOTE: I think we are moving away from these selectors
                    # since we are doing floating noticications now.
                    # "query_selector": "[role=main]",
                },
                "non_latest_version_warning": {
                    "enabled": Feature.ADDONS_NON_LATEST_VERSION_WARNING_DISABLED
                    not in project_features,
                    # NOTE: I think we are moving away from these selectors
                    # since we are doing floating noticications now.
                    # "query_selector": "[role=main]",
                    "versions": list(
                        versions_active_built_not_hidden.values_list("slug", flat=True)
                    ),
                },
                "doc_diff": {
                    "enabled": Feature.ADDONS_DOC_DIFF_DISABLED not in project_features,
                    # "http://test-builds-local.devthedocs.org/en/latest/index.html"
                    "base_url": resolver.resolve(
                        project=project,
                        version_slug=project.get_default_version(),
                        language=project.language,
                        filename=filename,
                    )
                    if filename
                    else None,
                    "root_selector": "[role=main]",
                    "inject_styles": True,
                    # NOTE: `base_host` and `base_page` are not required, since
                    # we are constructing the `base_url` in the backend instead
                    # of the frontend, as the doc-diff extension does.
                    "base_host": "",
                    "base_page": "",
                },
                "flyout": {
                    "enabled": Feature.ADDONS_FLYOUT_DISABLED not in project_features,
                    "translations": [
                        {
                            # TODO: name this field "display_name"
                            "slug": translation.language,
                            "url": f"/{translation.language}/",
                        }
                        for translation in project_translations
                    ],
                    "versions": [
                        {
                            # TODO: name this field "display_name"
                            "slug": version.slug,
                            "url": f"/{project.language}/{version.slug}/",
                        }
                        for version in versions_active_built_not_hidden
                    ],
                    "downloads": [
                        {
                            # TODO: name this field "display_name"
                            "name": name,
                            "url": url,
                        }
                        for name, url in version_downloads
                    ],
                    # TODO: find a way to get this data in a reliably way.
                    # We don't have a simple way to map a URL to a file in the repository.
                    # This feature may be deprecated/removed in this implementation since it relies
                    # on data injected at build time and sent as `docroot=`, `source_suffix=` and `page=`.
                    # Example URL:
                    #   /_/api/v2/footer_html/?project=weblate&version=latest&page=index&theme=furo&docroot=/docs/&source_suffix=.rst
                    # Data injected at:
                    #  https://github.com/rtfd/readthedocs-sphinx-ext/blob/7c60d1646c12ac0b83d61abfbdd5bcd77d324124/readthedocs_ext/_templates/readthedocs-insert.html.tmpl#L23
                    #
                    # "vcs": {
                    #     "url": "https://github.com",
                    #     "username": "readthedocs",
                    #     "repository": "test-builds",
                    #     "branch": version.identifier if version else None,
                    #     "filepath": "/docs/index.rst",
                    # },
                },
                "search": {
                    "enabled": Feature.ADDONS_SEARCH_DISABLED not in project_features,
                    "project": project.slug,
                    "version": version.slug if version else None,
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
                    ]
                    if version
                    else [],
                    "default_filter": f"subprojects:{project.slug}/{version.slug}"
                    if version
                    else None,
                },
                "hotkeys": {
                    "enabled": Feature.ADDONS_HOTKEYS_DISABLED not in project_features,
                    "doc_diff": {
                        "enabled": True,
                        "trigger": "KeyD",  # Could be something like "Ctrl + D"
                    },
                    "search": {
                        "enabled": True,
                        "trigger": "Slash",  # Could be something like "Ctrl + D"
                    },
                },
            },
        }

        # Update this data with the one generated at build time by the doctool
        if version and version.build_data:
            data.update(version.build_data)

        # Update this data with ethicalads
        if "readthedocsext.donate" in settings.INSTALLED_APPS:
            from readthedocsext.donate.utils import (  # noqa
                get_campaign_types,
                get_project_keywords,
                get_publisher,
                is_ad_free_project,
                is_ad_free_user,
            )

            data["addons"].update(
                {
                    "ethicalads": {
                        "enabled": Feature.ADDONS_ETHICALADS_DISABLED
                        not in project_features,
                        # NOTE: this endpoint is not authenticated, the user checks are done over an annonymous user for now
                        #
                        # NOTE: it requires ``settings.USE_PROMOS=True`` to return ``ad_free=false`` here
                        "ad_free": is_ad_free_user(AnonymousUser())
                        or is_ad_free_project(project),
                        "campaign_types": get_campaign_types(AnonymousUser(), project),
                        "keywords": get_project_keywords(project),
                        "publisher": get_publisher(project),
                    },
                }
            )

        return data

    def _v1(self, project, version, build, filename, user):
        return {
            "api_version": "1",
            "comment": "Undefined yet. Use v0 for now",
        }


class ReadTheDocsConfigJson(SettingsOverrideObject):
    _default_class = BaseReadTheDocsConfigJson
