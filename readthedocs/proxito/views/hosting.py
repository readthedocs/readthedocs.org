"""Views for hosting features."""

from functools import lru_cache

import packaging
import structlog
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.api.v3.serializers import BuildSerializer
from readthedocs.api.v3.serializers import ProjectSerializer
from readthedocs.api.v3.serializers import RelatedProjectSerializer
from readthedocs.api.v3.serializers import VersionSerializer
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.resolver import Resolver
from readthedocs.core.unresolver import UnresolverError
from readthedocs.core.unresolver import unresolver
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.filetreediff import get_diff
from readthedocs.projects.constants import ADDONS_FLYOUT_SORTING_CALVER
from readthedocs.projects.constants import ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN
from readthedocs.projects.constants import ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING
from readthedocs.projects.constants import ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE
from readthedocs.projects.models import Project
from readthedocs.projects.version_handling import comparable_version
from readthedocs.projects.version_handling import sort_versions_calver
from readthedocs.projects.version_handling import sort_versions_custom_pattern
from readthedocs.projects.version_handling import sort_versions_python_packaging


log = structlog.get_logger(__name__)  # noqa


ADDONS_VERSIONS_SUPPORTED = (1, 2)


class ClientError(Exception):
    VERSION_NOT_CURRENTLY_SUPPORTED = (
        "The version specified in 'api-version' is currently not supported"
    )
    VERSION_INVALID = "The version specifified in 'api-version' is invalid"
    PROJECT_NOT_FOUND = "There is no project with the 'project-slug' requested"


class IsAuthorizedToViewProject(permissions.BasePermission):
    """
    Checks if the user from the request has permissions to see the project.

    This is only valid if the view doesn't have a version,
    since the version permissions must be checked by the
    IsAuthorizedToViewVersion permission.
    """

    def has_permission(self, request, view):
        project = view._get_project()
        version = view._get_version()

        if version:
            return False

        has_access = Project.objects.public(user=request.user).filter(pk=project.pk).exists()
        return has_access


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
    permission_classes = [IsAuthorizedToViewProject | IsAuthorizedToViewVersion]
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

        if url:
            try:
                unresolved_url = unresolver.unresolve_url(url)
                # Project from the URL: if it's a subproject it will differ from
                # the main project got from the domain.
                project = unresolved_url.project
                version = unresolved_url.version
                filename = unresolved_url.filename
            except UnresolverError as exc:
                # If an exception is raised and there is a ``project`` in the
                # exception, it's a partial match. This could be because of an
                # invalid URL path, but on a valid project domain. In this case, we
                # continue with the ``project``, but without a ``version``.
                # Otherwise, we return 404 NOT FOUND.
                project = getattr(exc, "project", None)
        else:
            # When not sending "url", we require "project-slug" and "version-slug".
            project = get_object_or_404(Project, slug=project_slug)
            # We do allow hitting this URL without a valid version.
            # This is the same case than sending `?url=` with a partial match
            # (eg. invalid URL path).
            version = project.versions.filter(slug=version_slug).first()

        # A project is always required.
        if not project:
            raise Http404(ClientError.PROJECT_NOT_FOUND)

        # If we have a version, we also return its latest successful build.
        if version:
            # This query should use a particular index:
            # ``builds_build_version_id_state_date_success_12dfb214_idx``.
            # Otherwise, if the index is not used, the query gets too slow.
            build = (
                Build.objects.api(user=self.request.user)
                .filter(
                    project=project,
                    version=version,
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

    def dispatch(self, request, *args, **kwargs):
        # We check if the correct parameters are sent
        # in dispatch, since we want to return a useful error message
        # before checking for permissions.
        url = request.GET.get("url")
        project_slug = request.GET.get("project-slug")
        version_slug = request.GET.get("version-slug")
        if not url and (not project_slug or not version_slug):
            # NOTE: we don't use Response because we can't return it from
            # the dispatch method, we shuould refactor this to raise a subclass of APIException instead.
            return JsonResponse(
                {
                    "error": "'project-slug' and 'version-slug' GET attributes are required when not sending 'url'"
                },
                status=400,
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        url = request.GET.get("url")
        addons_version = request.GET.get("api-version")
        if not addons_version:
            return Response(
                {"error": "'api-version' GET attribute is required"},
                status=400,
            )
        try:
            addons_version = packaging.version.parse(addons_version)
            if addons_version.major not in ADDONS_VERSIONS_SUPPORTED:
                raise ClientError
        except packaging.version.InvalidVersion:
            return Response(
                {
                    "error": ClientError.VERSION_INVALID,
                },
                status=400,
            )
        except ClientError:
            return Response(
                {"error": ClientError.VERSION_NOT_CURRENTLY_SUPPORTED},
                status=400,
            )

        project, version, build, filename = self._resolve_resources()

        data = AddonsResponse().get(
            addons_version=addons_version,
            project=project,
            request=request,
            version=version,
            build=build,
            filename=filename,
            url=url,
        )
        return Response(data)


class RemoveFieldsMixin:
    """Mixin to remove fields from serializers."""

    FIELDS_TO_REMOVE = []

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
class RelatedProjectAddonsSerializer(RemoveFieldsMixin, RelatedProjectSerializer):
    FIELDS_TO_REMOVE = [
        "_links",
    ]


class ProjectAddonsSerializer(RemoveFieldsMixin, ProjectSerializer):
    FIELDS_TO_REMOVE = [
        "_links",
        # users and tags result in additional queries for fields that we don't use.
        "users",
        "tags",
    ]
    related_project_serializer = RelatedProjectAddonsSerializer


class VersionAddonsSerializer(RemoveFieldsMixin, VersionSerializer):
    FIELDS_TO_REMOVE = [
        "_links",
    ]


class BuildAddonsSerializer(RemoveFieldsMixin, BuildSerializer):
    FIELDS_TO_REMOVE = [
        "_links",
    ]


class AddonsResponseBase:
    def get(
        self,
        addons_version,
        project,
        request,
        version=None,
        build=None,
        filename=None,
        url=None,
    ):
        """
        Unique entry point to get the proper API response.

        It will evaluate the ``addons_version`` passed and decide which is the
        best JSON structure for that particular version.
        """
        if addons_version.major == 1:
            return self._v1(project, version, build, filename, url, request)

        if addons_version.major == 2:
            return self._v2(project, version, build, filename, url, request)

    def _get_versions(self, request, project):
        """
        Get all active for a project that the user has access to.

        This includes versions matching the following conditions:

        - The user has access to it
        - They are built
        - They are active
        - They are not hidden
        """
        return project.versions(manager=INTERNAL).public(
            user=request.user,
            only_active=True,
            only_built=True,
            include_hidden=False,
        )

    def _has_permission(self, request, version):
        """
        Check if user from the request is authorized to access `version`.

        This is mainly to be overridden in .com to make use of
        the auth backends in the proxied API.
        """
        return True

    def _v1(self, project, version, build, filename, url, request):
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
        sorted_versions_active_built_not_hidden = Version.objects.none()

        versions_active_built_not_hidden = self._get_versions(request, project).order_by("-slug")
        sorted_versions_active_built_not_hidden = versions_active_built_not_hidden
        if not project.supports_multiple_versions:
            # Return only one version when the project doesn't support multiple versions.
            # That version is the only one the project serves.
            sorted_versions_active_built_not_hidden = (
                sorted_versions_active_built_not_hidden.filter(slug=project.get_default_version())
            )
        else:
            if project.addons.flyout_sorting == ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE:
                sorted_versions_active_built_not_hidden = sorted(
                    versions_active_built_not_hidden,
                    key=lambda version: comparable_version(
                        version.verbose_name,
                        repo_type=project.repo_type,
                    ),
                    reverse=True,
                )
            elif project.addons.flyout_sorting == ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING:
                sorted_versions_active_built_not_hidden = sort_versions_python_packaging(
                    versions_active_built_not_hidden,
                    project.addons.flyout_sorting_latest_stable_at_beginning,
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

        search_default_filter = f"project:{project.slug}"
        if version:
            search_default_filter = f"project:{project.slug}/{version.slug}"

        data = {
            "api_version": "1",
            "projects": self._get_projects_response(
                request=request, project=project, version=version, resolver=resolver
            ),
            "versions": {
                "current": VersionAddonsSerializer(
                    version,
                    resolver=resolver,
                ).data
                if version
                else None,
                # These are "sorted active, built, not hidden versions"
                "active": VersionAddonsSerializer(
                    sorted_versions_active_built_not_hidden,
                    resolver=resolver,
                    many=True,
                ).data,
            },
            "builds": {
                "current": BuildAddonsSerializer(build).data if build else None,
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
                "resolver": {
                    "filename": filename,
                },
            },
            # TODO: the ``features`` is not polished and we expect to change drastically.
            # Mainly, all the fields including a Project, Version or Build will use the exact same
            # serializer than the keys ``project``, ``version`` and ``build`` from the top level.
            "addons": {
                "options": {
                    "load_when_embedded": project.addons.options_load_when_embedded,
                    "root_selector": project.addons.options_root_selector,
                },
                "analytics": {
                    "enabled": project.addons.analytics_enabled,
                    # TODO: consider adding this field into the ProjectSerializer itself.
                    # NOTE: it seems we are removing this feature,
                    # so we may not need the ``code`` attribute here
                    # https://github.com/readthedocs/readthedocs.org/issues/9530
                    "code": project.analytics_code,
                },
                "notifications": {
                    "enabled": project.addons.notifications_enabled,
                    "show_on_latest": project.addons.notifications_show_on_latest,
                    "show_on_non_stable": project.addons.notifications_show_on_non_stable,
                    "show_on_external": project.addons.notifications_show_on_external,
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
                    "position": project.addons.flyout_position,
                },
                "customscript": {
                    "enabled": project.addons.customscript_enabled,
                    "src": project.addons.customscript_src,
                },
                "search": {
                    "enabled": project.addons.search_enabled,
                    # TODO: figure it out where this data comes from.
                    #
                    # Originally, this was thought to be customizable by the user
                    # adding these filters from the Admin UI.
                    #
                    # I'm removing this feature for now until we implement it correctly.
                    "filters": [
                        # NOTE: this is an example of the structure of the this object.
                        # It contains the name of the filter and the search syntax to prepend
                        # to the user's query.
                        # It uses "Search query sintax":
                        # https://docs.readthedocs.io/en/stable/server-side-search/syntax.html
                        # [
                        #     "Include subprojects",
                        #     f"subprojects:{project.slug}/{version.slug}",
                        # ],
                    ],
                    "default_filter": search_default_filter,
                },
                "linkpreviews": {
                    "enabled": project.addons.linkpreviews_enabled,
                    "selector": project.addons.linkpreviews_selector,
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
                "filetreediff": {
                    "enabled": project.addons.filetreediff_enabled,
                },
            },
        }

        if version:
            response = self._get_filetreediff_response(
                request=request,
                project=project,
                version=version,
                resolver=resolver,
            )
            if response:
                data["addons"]["filetreediff"].update(response)

            # Show the subprojects filter on the parent project and subproject
            # TODO: Remove these queries and try to find a way to get this data
            # from the resolver, which has already done these queries.
            # TODO: Replace this fixed filters with the work proposed in
            # https://github.com/readthedocs/addons/issues/22
            if project.subprojects.exists():
                data["addons"]["search"]["filters"].append(
                    [
                        "Include subprojects",
                        f"subprojects:{project.slug}/{version.slug}",
                        True,
                    ]
                )
            elif project.superprojects.exists():
                superproject = project.superprojects.first().parent
                data["addons"]["search"]["filters"].append(
                    [
                        "Include subprojects",
                        f"subprojects:{superproject.slug}/{version.slug}",
                        True,
                    ]
                )

        # DocDiff depends on `url=` GET attribute.
        # This attribute allows us to know the exact filename where the request was made.
        # If we don't know the filename, we cannot return the data required by DocDiff to work.
        # In that case, we just don't include the `doc_diff` object in the response.
        if url:
            base_version_slug = (
                project.addons.options_base_version.slug
                if project.addons.options_base_version
                else LATEST
            )
            data["addons"].update(
                {
                    "doc_diff": {
                        "enabled": project.addons.doc_diff_enabled,
                        # "http://test-builds-local.devthedocs.org/en/latest/index.html"
                        "base_url": resolver.resolve(
                            project=project,
                            version_slug=base_version_slug,
                            language=project.language,
                            filename=filename,
                        )
                        if filename
                        else None,
                        "inject_styles": True,
                    },
                }
            )

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
                        "ad_free": is_ad_free_user(AnonymousUser()) or is_ad_free_project(project),
                        "campaign_types": get_campaign_types(AnonymousUser(), project),
                        "keywords": get_project_keywords(project),
                        "publisher": get_publisher(project),
                    },
                }
            )

        return data

    def _get_projects_response(self, *, request, project, version, resolver):
        main_project = project.main_language_project or project

        translation_filter = Q(pk__in=main_project.translations.all())
        # Include main project as translation if the current project is one of the translations
        if main_project != project:
            translation_filter |= Q(pk=main_project.pk)

        translations_qs = (
            Project.objects.public(user=request.user)
            .filter(translation_filter)
            # Exclude the current project since we don't want to return itself as a translation
            .exclude(pk=project.pk)
            .order_by("language")
            .select_related("main_language_project")
            # NOTE: there is no need to prefetch superprojects,
            # as translations are not expected to have superprojects,
            # and the serializer already checks for that.
        )
        # NOTE: we check if there are translations first,
        # otherwise evaluating the queryset will be more expensive
        # even if there are no results. Django optimizes the queryset
        # if only we need to check if there are results or not.
        if translations_qs.exists():
            translations = ProjectAddonsSerializer(
                translations_qs,
                resolver=resolver,
                version=version,
                many=True,
            ).data
        else:
            translations = []

        return {
            "current": ProjectAddonsSerializer(
                project,
                resolver=resolver,
                version=version,
            ).data,
            "translations": translations,
        }

    def _get_filetreediff_response(self, *, request, project, version, resolver):
        """
        Get the file tree diff response for the given version.

        This response is only enabled for external versions,
        we do the comparison between the current version and the latest version.
        """
        if not version.is_external and not settings.RTD_FILETREEDIFF_ALL:
            return None

        if not project.addons.filetreediff_enabled:
            return None

        base_version = project.addons.options_base_version or project.get_latest_version()
        if not base_version or not self._has_permission(request=request, version=base_version):
            return None

        diff = get_diff(current_version=version, base_version=base_version)
        if not diff:
            return None

        def _serialize_files(files):
            return [
                {
                    "filename": file.path,
                    "urls": {
                        "current": resolver.resolve_version(
                            project=project,
                            filename=file.path,
                            version=version,
                        ),
                        "base": resolver.resolve_version(
                            project=project,
                            filename=file.path,
                            version=base_version,
                        ),
                    },
                }
                for file in files
            ]

        return {
            "outdated": diff.outdated,
            "diff": {
                "added": _serialize_files(diff.added),
                "deleted": _serialize_files(diff.deleted),
                "modified": _serialize_files(diff.modified),
            },
        }

    def _v2(self, project, version, build, filename, url, user):
        return {
            "api_version": "2",
            "comment": "Undefined yet. Use v1 for now",
        }


class AddonsResponse(SettingsOverrideObject):
    _default_class = AddonsResponseBase


class ReadTheDocsConfigJson(SettingsOverrideObject):
    _default_class = BaseReadTheDocsConfigJson
