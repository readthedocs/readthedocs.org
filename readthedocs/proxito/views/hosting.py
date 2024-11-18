"""Views for hosting features."""
from functools import lru_cache

import packaging
import structlog
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions
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
from readthedocs.builds.models import Build, Version
from readthedocs.core.resolver import Resolver
from readthedocs.core.unresolver import UnresolverError, unresolver
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.filetreediff import get_diff
from readthedocs.projects.constants import (
    ADDONS_FLYOUT_SORTING_CALVER,
    ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN,
    ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING,
    ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE,
)
from readthedocs.projects.models import AddonsConfig, Feature, Project
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

        has_access = (
            Project.objects.public(user=request.user).filter(pk=project.pk).exists()
        )
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
            version = get_object_or_404(project.versions.all(), slug=version_slug)

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
            addons_version=addons_version,
            project=project,
            request=request,
            version=version,
            build=build,
            filename=filename,
            url=url,
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
        return Version.internal.public(
            project=project,
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
        user = request.user

        # Automatically create an AddonsConfig with the default values for
        # projects that don't have one already
        AddonsConfig.objects.get_or_create(project=project)

        versions_active_built_not_hidden = (
            self._get_versions(request, project)
            .select_related("project")
            .order_by("-slug")
        )
        sorted_versions_active_built_not_hidden = versions_active_built_not_hidden
        if not project.supports_multiple_versions:
            # Return only one version when the project doesn't support multiple versions.
            # That version is the only one the project serves.
            sorted_versions_active_built_not_hidden = (
                sorted_versions_active_built_not_hidden.filter(
                    slug=project.get_default_version()
                )
            )
        else:
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
                    reverse=True,
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

        # Exclude the current project since we don't want to return itself as a translation
        project_translations = (
            Project.objects.public(user=user)
            .filter(pk__in=main_project.translations.all())
            .exclude(slug=project.slug)
        )

        # Include main project as translation if the current project is one of the translations
        if project != main_project:
            project_translations |= Project.objects.public(user=user).filter(
                slug=main_project.slug
            )
        project_translations = project_translations.order_by("language").select_related(
            "main_language_project"
        )

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
                "options": {
                    "load_when_embedded": project.addons.options_load_when_embedded,
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
                    "default_filter": f"project:{project.slug}/{version.slug}"
                    if version
                    else None,
                },
                "linkpreviews": {
                    "enabled": project.addons.linkpreviews_enabled,
                    "root_selector": project.addons.linkpreviews_root_selector
                    or project.addons.LINKPREVIEWS_DEFAULT_ROOT_SELECTOR,
                    "doctool": {
                        "name": project.addons.linkpreviews_doctool_name,
                        "version": project.addons.linkpreviews_doctool_version,
                    },
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
                    "enabled": False,
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
                    ]
                )
            if project.superprojects.exists():
                superproject = project.superprojects.first().parent
                data["addons"]["search"]["filters"].append(
                    [
                        "Include subprojects",
                        f"subprojects:{superproject.slug}/{version.slug}",
                    ]
                )

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

    def _get_filetreediff_response(self, *, request, project, version, resolver):
        """
        Get the file tree diff response for the given version.

        This response is only enabled for external versions,
        we do the comparison between the current version and the latest version.
        """
        if not version.is_external:
            return None

        if not project.has_feature(Feature.GENERATE_MANIFEST_FOR_FILE_TREE_DIFF):
            return None

        latest_version = project.get_latest_version()
        if not latest_version or not self._has_permission(
            request=request, version=latest_version
        ):
            return None

        diff = get_diff(version_a=version, version_b=latest_version)
        if not diff:
            return None

        return {
            "enabled": True,
            "outdated": diff.outdated,
            "diff": {
                "added": [
                    {
                        "filename": filename,
                        "urls": {
                            "current": resolver.resolve_version(
                                project=project,
                                filename=filename,
                                version=version,
                            ),
                            "base": resolver.resolve_version(
                                project=project,
                                filename=filename,
                                version=latest_version,
                            ),
                        },
                    }
                    for filename in diff.added
                ],
                "deleted": [
                    {
                        "filename": filename,
                        "urls": {
                            "current": resolver.resolve_version(
                                project=project,
                                filename=filename,
                                version=version,
                            ),
                            "base": resolver.resolve_version(
                                project=project,
                                filename=filename,
                                version=latest_version,
                            ),
                        },
                    }
                    for filename in diff.deleted
                ],
                "modified": [
                    {
                        "filename": filename,
                        "urls": {
                            "current": resolver.resolve_version(
                                project=project,
                                filename=filename,
                                version=version,
                            ),
                            "base": resolver.resolve_version(
                                project=project,
                                filename=filename,
                                version=latest_version,
                            ),
                        },
                    }
                    for filename in diff.modified
                ],
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
