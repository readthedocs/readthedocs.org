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
from readthedocs.builds.constants import BUILD_STATE_FINISHED, LATEST
from readthedocs.builds.models import Version
from readthedocs.core.resolver import Resolver
from readthedocs.core.unresolver import UnresolverError, unresolver
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.constants import (
    ADDONS_FLYOUT_SORTING_CALVER,
    ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN,
    ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING,
    ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE,
)
from readthedocs.projects.models import AddonsConfig, Project
from readthedocs.projects.version_handling import (
    comparable_version,
    sort_versions_calver,
    sort_versions_custom_pattern,
    sort_versions_python_packaging,
)

log = structlog.get_logger(__name__)  # noqa


ADDONS_VERSIONS_SUPPORTED = (1, 2)


class ClientError(Exception):
    VERSION_NOT_CURRENTLY_SUPPORTED = (
        "The version specified in 'api-version' is currently not supported"
    )
    VERSION_INVALID = "The version specifified in 'api-version' is invalid"
    PROJECT_NOT_FOUND = "There is no project with the 'project-slug' requested"


class BaseReadTheDocsConfigJson(CDNCacheTagsMixin, APIView):

    """
    API response consumed by our JavaScript client.

    The code for the JavaScript client lives at:
      https://github.com/readthedocs/addons/

    Attributes:

      api-version (required): API JSON structure version (e.g. ``0``, ``1``, ``2``).

      project-slug (required): slug of the project.
        Optional if "url" is sent.

      version-slug (required): slug of the version.
        Optional if "url" is sent.

      url (optional): absolute URL from where the request is performed.
        When sending "url" attribute, "project-slug" and "version-slug" are ignored.
        (e.g. ``window.location.href``).

      client-version (optional): JavaScript client version (e.g. ``0.6.0``).
    """

    http_method_names = ["get"]
    permission_classes = [IsAuthorizedToViewVersion]
    renderer_classes = [JSONRenderer]
    project_cache_tag = "rtd-addons"

    @lru_cache(maxsize=1)
    def _resolve_resources(self):
        url = self.request.GET.get("url")
        project_slug = self.request.GET.get("project-slug")
        version_slug = self.request.GET.get("version-slug")

        project = None
        version = None
        build = None
        filename = None

        unresolved_domain = self.request.unresolved_domain

        # Main project from the domain.
        project = unresolved_domain.project

        if url:
            try:
                unresolved_url = unresolver.unresolve_url(url)
                # Project from the URL: if it's a subproject it will differ from
                # the main project got from the domain.
                project = unresolved_url.project
                version = unresolved_url.version
                filename = unresolved_url.filename
                # This query should use a particular index:
                # ``builds_build_version_id_state_date_success_12dfb214_idx``.
                # Otherwise, if the index is not used, the query gets too slow.
                build = (
                    version.builds.filter(
                        success=True,
                        state=BUILD_STATE_FINISHED,
                    )
                    .select_related("project", "version")
                    .first()
                )

            except UnresolverError as exc:
                # If an exception is raised and there is a ``project`` in the
                # exception, it's a partial match. This could be because of an
                # invalid URL path, but on a valid project domain. In this case, we
                # continue with the ``project``, but without a ``version``.
                # Otherwise, we return 404 NOT FOUND.
                project = getattr(exc, "project", None)
                if not project:
                    raise Http404() from exc

        else:
            project = Project.objects.filter(slug=project_slug).first()
            version = (
                Version.objects.filter(slug=version_slug, project=project)
                .select_related("project")
                .first()
            )
            if version:
                build = (
                    version.builds.filter(
                        success=True,
                        state=BUILD_STATE_FINISHED,
                    )
                    .select_related("project", "version")
                    .first()
                )

        return project, version, build, filename

    def _get_project(self):
        project, _, _, _ = self._resolve_resources()
        return project

    def _get_version(self):
        _, version, _, _ = self._resolve_resources()
        return version

    def get(self, request, format=None):
        url = request.GET.get("url")
        project_slug = request.GET.get("project-slug")
        version_slug = request.GET.get("version-slug")
        if not url:
            if not project_slug or not version_slug:
                return JsonResponse(
                    {
                        "error": "'project-slug' and 'version-slug' GET attributes are required when not sending 'url'"
                    },
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
        if not project:
            return JsonResponse(
                {"error": ClientError.PROJECT_NOT_FOUND},
                status=404,
            )

        data = AddonsResponse().get(
            addons_version,
            project,
            version,
            build,
            filename,
            url,
            user=request.user,
        )
        return JsonResponse(data, json_dumps_params={"indent": 4, "sort_keys": True})


class NoLinksMixin:

    """Mixin to remove conflicting fields from serializers."""

    FIELDS_TO_REMOVE = ("_links",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.FIELDS_TO_REMOVE:
            if field in self.fields:
                del self.fields[field]

            if field in self.Meta.fields:
                del self.Meta.fields[self.Meta.fields.index(field)]


# NOTE: the following serializers are required only to remove some fields we
# can't expose yet in this API endpoint because it's running under El Proxito
# which cannot resolve URLs pointing to the APIv3 because they are not defined
# on El Proxito.
#
# See https://github.com/readthedocs/readthedocs-ops/issues/1323
class ProjectSerializerNoLinks(NoLinksMixin, ProjectSerializer):
    def __init__(self, *args, **kwargs):
        resolver = kwargs.pop("resolver", Resolver())
        super().__init__(
            *args,
            resolver=resolver,
            **kwargs,
        )


class VersionSerializerNoLinks(NoLinksMixin, VersionSerializer):
    def __init__(self, *args, **kwargs):
        resolver = kwargs.pop("resolver", Resolver())
        super().__init__(
            *args,
            resolver=resolver,
            version_serializer=VersionSerializerNoLinks,
            **kwargs,
        )


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
        url=None,
        user=None,
    ):
        """
        Unique entry point to get the proper API response.

        It will evaluate the ``addons_version`` passed and decide which is the
        best JSON structure for that particular version.
        """
        if addons_version.major == 1:
            return self._v1(project, version, build, filename, url, user)

        if addons_version.major == 2:
            return self._v2(project, version, build, filename, url, user)

    def _v1(self, project, version, build, filename, url, user):
        """
        Initial JSON data structure consumed by the JavaScript client.

        This response is definitely in *alpha* state currently and shouldn't be
        used for anyone to customize their documentation or the integration
        with the Read the Docs JavaScript client. It's under active development
        and anything can change without notice.

        It tries to follow some similarity with the APIv3 for already-known resources
        (Project, Version, Build, etc).
        """
        resolver = Resolver()
        versions_active_built_not_hidden = Version.objects.none()
        sorted_versions_active_built_not_hidden = (
            versions_active_built_not_hidden
        ) = Version.objects.none()

        # Automatically create an AddonsConfig with the default values for
        # projects that don't have one already
        AddonsConfig.objects.get_or_create(project=project)

        if project.supports_multiple_versions:
            versions_active_built_not_hidden = (
                Version.internal.public(
                    project=project,
                    only_active=True,
                    only_built=True,
                    user=user,
                )
                .exclude(hidden=True)
                .select_related("project")
                .order_by("slug")
            )
            sorted_versions_active_built_not_hidden = versions_active_built_not_hidden

            if (
                project.addons.flyout_sorting
                == ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE
            ):
                sorted_versions_active_built_not_hidden = sorted(
                    versions_active_built_not_hidden,
                    key=lambda version: comparable_version(
                        version.verbose_name,
                        repo_type=project.repo_type,
                    ),
                )
            elif (
                project.addons.flyout_sorting == ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING
            ):
                sorted_versions_active_built_not_hidden = (
                    sort_versions_python_packaging(
                        versions_active_built_not_hidden,
                        project.addons.flyout_sorting_latest_stable_at_beginning,
                    )
                )
            elif project.addons.flyout_sorting == ADDONS_FLYOUT_SORTING_CALVER:
                sorted_versions_active_built_not_hidden = sort_versions_calver(
                    versions_active_built_not_hidden,
                    project.addons.flyout_sorting_latest_stable_at_beginning,
                )
            elif project.addons.flyout_sorting == ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN:
                sorted_versions_active_built_not_hidden = sort_versions_custom_pattern(
                    versions_active_built_not_hidden,
                    project.addons.flyout_sorting_custom_pattern,
                    project.addons.flyout_sorting_latest_stable_at_beginning,
                )

        main_project = project.main_language_project or project
        project_translations = main_project.translations.all().order_by("language")

        data = {
            "api_version": "1",
            "projects": {
                "current": ProjectSerializerNoLinks(
                    project,
                    resolver=resolver,
                    version_slug=version.slug if version else None,
                ).data,
                "translations": ProjectSerializerNoLinks(
                    project_translations,
                    resolver=resolver,
                    version_slug=version.slug if version else None,
                    many=True,
                ).data,
            },
            "versions": {
                "current": VersionSerializerNoLinks(
                    version,
                    resolver=resolver,
                ).data
                if version
                else None,
                # These are "sorted active, built, not hidden versions"
                "active": VersionSerializerNoLinks(
                    sorted_versions_active_built_not_hidden,
                    resolver=resolver,
                    many=True,
                ).data,
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
                    "enabled": project.addons.analytics_enabled,
                    # TODO: consider adding this field into the ProjectSerializer itself.
                    # NOTE: it seems we are removing this feature,
                    # so we may not need the ``code`` attribute here
                    # https://github.com/readthedocs/readthedocs.org/issues/9530
                    "code": project.analytics_code,
                },
                "external_version_warning": {
                    "enabled": project.addons.external_version_warning_enabled,
                    # NOTE: I think we are moving away from these selectors
                    # since we are doing floating noticications now.
                    # "query_selector": "[role=main]",
                },
                "non_latest_version_warning": {
                    "enabled": project.addons.stable_latest_version_warning_enabled,
                    # NOTE: I think we are moving away from these selectors
                    # since we are doing floating noticications now.
                    # "query_selector": "[role=main]",
                },
                "flyout": {
                    "enabled": project.addons.flyout_enabled,
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
                    "enabled": project.addons.search_enabled,
                    # TODO: figure it out where this data comes from
                    "filters": [
                        [
                            "Include subprojects",
                            f"subprojects:{project.slug}/{version.slug}",
                        ],
                    ]
                    if version
                    else [],
                    "default_filter": f"project:{project.slug}/{version.slug}"
                    if version
                    else None,
                },
                "hotkeys": {
                    "enabled": project.addons.hotkeys_enabled,
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

        # DocDiff depends on `url=` GET attribute.
        # This attribute allows us to know the exact filename where the request was made.
        # If we don't know the filename, we cannot return the data required by DocDiff to work.
        # In that case, we just don't include the `doc_diff` object in the response.
        if url:
            data["addons"].update(
                {
                    "doc_diff": {
                        "enabled": project.addons.doc_diff_enabled,
                        # "http://test-builds-local.devthedocs.org/en/latest/index.html"
                        "base_url": resolver.resolve(
                            project=project,
                            # NOTE: we are using LATEST version to compare against to for now.
                            # Ideally, this should be configurable by the user.
                            version_slug=LATEST,
                            language=project.language,
                            filename=filename,
                        )
                        if filename
                        else None,
                        "root_selector": project.addons.doc_diff_root_selector,
                        "inject_styles": True,
                        # NOTE: `base_host` and `base_page` are not required, since
                        # we are constructing the `base_url` in the backend instead
                        # of the frontend, as the doc-diff extension does.
                        "base_host": "",
                        "base_page": "",
                    },
                }
            )

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
                        "enabled": project.addons.ethicalads_enabled,
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

    def _v2(self, project, version, build, filename, url, user):
        return {
            "api_version": "2",
            "comment": "Undefined yet. Use v1 for now",
        }


class ReadTheDocsConfigJson(SettingsOverrideObject):
    _default_class = BaseReadTheDocsConfigJson
