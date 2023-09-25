"""Endpoints for listing Projects, Versions, Builds, etc."""
import json

import structlog
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, Case, Value, When
from django.http import Http404
from django.template.loader import render_to_string
from rest_framework import decorators, status, viewsets
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.response import Response

from readthedocs.api.v2.permissions import HasBuildAPIKey, IsOwner, ReadOnlyPermission
from readthedocs.api.v2.utils import normalize_build_command
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.oauth.services import registry
from readthedocs.projects.models import Domain, Project
from readthedocs.storage import build_commands_storage

from ..serializers import (
    BuildAdminReadOnlySerializer,
    BuildAdminSerializer,
    BuildCommandSerializer,
    BuildSerializer,
    DomainSerializer,
    ProjectAdminSerializer,
    ProjectSerializer,
    RemoteOrganizationSerializer,
    RemoteRepositorySerializer,
    SocialAccountSerializer,
    VersionAdminSerializer,
    VersionSerializer,
)
from ..utils import (
    ProjectPagination,
    RemoteOrganizationPagination,
    RemoteProjectPagination,
)

log = structlog.get_logger(__name__)


class PlainTextBuildRenderer(BaseRenderer):

    """
    Custom renderer for text/plain format.

    charset is 'utf-8' by default.
    """

    media_type = "text/plain"
    format = "txt"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        if not response or response.exception:
            return data.get("detail", "").encode(self.charset)
        data = render_to_string(
            "restapi/log.txt",
            {"build": data},
        )
        return data.encode(self.charset)


class DisableListEndpoint:

    """
    Helper to disable APIv2 listing endpoint.

    We are disablng the listing endpoint because it could cause DOS without
    using any type of filtering.

    This class disables these endpoints except:

     - version resource when passing ``?project__slug=``
     - build resource when using ``?commit=``

    All the other type of listings are disabled and return 409 CONFLICT with an
    error message pointing the user to APIv3.
    """

    def list(self, *args, **kwargs):
        # Using private repos will list resources the user has access to.
        if settings.ALLOW_PRIVATE_REPOS:
            return super().list(*args, **kwargs)

        disabled = True

        # NOTE: keep list endpoint that specifies a resource
        if any(
            [
                self.basename == "version" and "project__slug" in self.request.GET,
                self.basename == "build"
                and (
                    "commit" in self.request.GET or "project__slug" in self.request.GET
                ),
                self.basename == "project" and "slug" in self.request.GET,
            ]
        ):
            disabled = False

        if not disabled:
            return super().list(*args, **kwargs)

        return Response(
            {
                "error": "disabled",
                "msg": (
                    "List endpoint have been disabled due to heavy resource usage. "
                    "Take into account than APIv2 is planned to be deprecated soon. "
                    "Please use APIv3: https://docs.readthedocs.io/page/api/v3.html"
                ),
            },
            status=status.HTTP_410_GONE,
        )


class UserSelectViewSet(viewsets.ReadOnlyModelViewSet):

    """
    View set that varies serializer class based on request user credentials.

    Viewsets using this class should have an attribute `admin_serializer_class`,
    which is a serializer that might have more fields that only the builders
    require. If the request is using a Build API key, this class will be returned instead.

    By default read-only endpoints will be allowed,
    to allow write endpoints, inherit from the proper ``rest_framework.mixins.*`` classes.
    """

    def get_serializer_class(self):
        try:
            if self.request.build_api_key and self.admin_serializer_class is not None:
                return self.admin_serializer_class
        except AttributeError:
            pass
        return self.serializer_class

    def get_queryset_for_api_key(self, api_key):
        """Queryset used when an API key is used in the request."""
        raise NotImplementedError

    def get_queryset(self):
        """
        Filter objects by user or API key.

        If an API key is present, we filter by the project associated with the key.
        Otherwise, we filter using our API manager method.

        With this we check if the user/api key is authorized to acccess the object.
        """
        api_key = getattr(self.request, "build_api_key", None)
        if api_key:
            return self.get_queryset_for_api_key(api_key)
        return self.model.objects.api(self.request.user)


class ProjectViewSet(DisableListEndpoint, UpdateModelMixin, UserSelectViewSet):

    """List, filter, etc, Projects."""

    permission_classes = [HasBuildAPIKey | ReadOnlyPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = ProjectSerializer
    admin_serializer_class = ProjectAdminSerializer
    model = Project
    pagination_class = ProjectPagination
    filterset_fields = ("slug",)

    @decorators.action(detail=True)
    def translations(self, *_, **__):
        translations = self.get_object().translations.all()
        return Response(
            {
                "translations": ProjectSerializer(translations, many=True).data,
            }
        )

    @decorators.action(detail=True)
    def subprojects(self, request, **kwargs):
        project = self.get_object()
        rels = project.subprojects.all()
        children = [rel.child for rel in rels]
        return Response(
            {
                "subprojects": ProjectSerializer(children, many=True).data,
            }
        )

    @decorators.action(detail=True)
    def active_versions(self, request, **kwargs):
        project = self.get_object()
        versions = project.versions(manager=INTERNAL).filter(active=True)
        return Response(
            {
                "versions": VersionSerializer(versions, many=True).data,
            }
        )

    @decorators.action(detail=True)
    def canonical_url(self, request, **kwargs):
        project = self.get_object()
        return Response(
            {
                "url": project.get_docs_url(),
            }
        )

    def get_queryset_for_api_key(self, api_key):
        return self.model.objects.filter(pk=api_key.project.pk)


class VersionViewSet(DisableListEndpoint, UpdateModelMixin, UserSelectViewSet):
    permission_classes = [HasBuildAPIKey | ReadOnlyPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = VersionSerializer
    admin_serializer_class = VersionAdminSerializer
    model = Version
    filterset_fields = (
        "active",
        "project__slug",
    )

    def get_queryset_for_api_key(self, api_key):
        return self.model.objects.filter(project=api_key.project)

    def get_queryset(self):
        return super().get_queryset().select_related("project")


class BuildViewSet(DisableListEndpoint, UpdateModelMixin, UserSelectViewSet):
    permission_classes = [HasBuildAPIKey | ReadOnlyPermission]
    renderer_classes = (JSONRenderer, PlainTextBuildRenderer)
    model = Build
    filterset_fields = ("project__slug", "commit")

    def get_serializer_class(self):
        """
        Return the proper serializer for UI and Admin.

        This ViewSet has a sligtly different pattern since we want to
        pre-process the `command` field before returning it to the user, and we
        also want to have a specific serializer for admins.
        """
        if self.request.build_api_key:
            # Logic copied from `UserSelectViewSet.get_serializer_class`
            # and extended to choose serializer from self.action
            if self.action not in ["list", "retrieve"]:
                return BuildAdminSerializer  # Staff write-only
            return BuildAdminReadOnlySerializer  # Staff read-only
        return BuildSerializer  # Non-staff

    @decorators.action(
        detail=False,
        permission_classes=[HasBuildAPIKey],
        methods=["get"],
    )
    def concurrent(self, request, **kwargs):
        project_slug = request.GET.get("project__slug")
        build_api_key = request.build_api_key
        if project_slug != build_api_key.project.slug:
            log.warning(
                "Project slug doesn't match the one attached to the API key.",
                api_key_id=build_api_key.id,
                project_slug=project_slug,
            )
            raise Http404()
        project = build_api_key.project
        limit_reached, concurrent, max_concurrent = Build.objects.concurrent(project)
        data = {
            "limit_reached": limit_reached,
            "concurrent": concurrent,
            "max_concurrent": max_concurrent,
        }
        return Response(data)

    def retrieve(self, *args, **kwargs):
        """
        Retrieves command data from storage.

        This uses files from storage to get the JSON,
        and replaces the ``commands`` part of the response data.
        """
        if not settings.RTD_SAVE_BUILD_COMMANDS_TO_STORAGE:
            return super().retrieve(*args, **kwargs)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if instance.cold_storage:
            storage_path = "{date}/{id}.json".format(
                date=str(instance.date.date()),
                id=instance.id,
            )
            if build_commands_storage.exists(storage_path):
                try:
                    json_resp = build_commands_storage.open(storage_path).read()
                    data["commands"] = json.loads(json_resp)

                    # Normalize commands in the same way than when returning
                    # them using the serializer
                    for buildcommand in data["commands"]:
                        buildcommand["command"] = normalize_build_command(
                            buildcommand["command"],
                            instance.project.slug,
                            instance.version.slug,
                        )
                except Exception:
                    log.exception(
                        "Failed to read build data from storage.",
                        path=storage_path,
                    )
        return Response(data)

    @decorators.action(
        detail=True,
        permission_classes=[HasBuildAPIKey],
        methods=["post"],
    )
    def reset(self, request, **kwargs):
        """Reset the build so it can be re-used when re-trying."""
        instance = self.get_object()
        instance.reset()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset_for_api_key(self, api_key):
        return self.model.objects.filter(project=api_key.project)


class BuildCommandViewSet(DisableListEndpoint, CreateModelMixin, UserSelectViewSet):
    parser_classes = [JSONParser, MultiPartParser]
    permission_classes = [HasBuildAPIKey | ReadOnlyPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = BuildCommandSerializer
    model = BuildCommandResult

    def perform_create(self, serializer):
        """Restrict creation to builds attached to the project from the api key."""
        build_pk = serializer.validated_data["build"].pk
        build_api_key = self.request.build_api_key
        if not build_api_key.project.builds.filter(pk=build_pk).exists():
            raise PermissionDenied()

        if BuildCommandResult.objects.filter(
            build=serializer.validated_data["build"],
            start_time=serializer.validated_data["start_time"],
        ).exists():
            log.warning("Build command is duplicated. Skipping...")
            return

        return super().perform_create(serializer)

    def get_queryset_for_api_key(self, api_key):
        return self.model.objects.filter(build__project=api_key.project)


class DomainViewSet(DisableListEndpoint, UserSelectViewSet):
    permission_classes = [ReadOnlyPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = DomainSerializer
    model = Domain


class RemoteOrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = RemoteOrganizationSerializer
    model = RemoteOrganization
    pagination_class = RemoteOrganizationPagination

    def get_queryset(self):
        return (
            self.model.objects.api(self.request.user)
            .filter(
                remote_organization_relations__account__provider__in=[
                    service.adapter.provider_id for service in registry
                ]
            )
            .distinct()
        )


class RemoteRepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = RemoteRepositorySerializer
    model = RemoteRepository
    pagination_class = RemoteProjectPagination

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.model.objects.none()

        # TODO: Optimize this query after deployment
        query = self.model.objects.api(self.request.user).annotate(
            admin=Case(
                When(
                    remote_repository_relations__user=self.request.user,
                    remote_repository_relations__admin=True,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        full_name = self.request.query_params.get("full_name")
        if full_name is not None:
            query = query.filter(full_name__icontains=full_name)
        org = self.request.query_params.get("org", None)
        if org is not None:
            query = query.filter(organization__pk=org)

        own = self.request.query_params.get("own", None)
        if own is not None:
            query = query.filter(
                remote_repository_relations__account__provider=own,
                organization=None,
            )

        query = query.filter(
            remote_repository_relations__account__provider__in=[
                service.adapter.provider_id for service in registry
            ],
        ).distinct()

        # optimizes for the RemoteOrganizationSerializer
        query = query.select_related("organization").order_by(
            "organization__name", "full_name"
        )

        return query


class SocialAccountViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = SocialAccountSerializer
    model = SocialAccount

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user.pk)
