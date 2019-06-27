import django_filters.rest_framework as filters
from django.utils.safestring import mark_safe
from rest_flex_fields.views import FlexFieldsMixin
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.metadata import SimpleMetadata
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet, ModelViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project
from readthedocs.redirects.models import Redirect

from .filters import BuildFilter, ProjectFilter, VersionFilter
from .mixins import ProjectQuerySetMixin
from .permissions import PublicDetailPrivateListing, IsProjectAdmin
from .renderers import AlphabeticalSortedJSONRenderer
from .serializers import (
    BuildCreateSerializer,
    BuildSerializer,
    ProjectSerializer,
    ProjectCreateSerializer,
    RedirectCreateSerializer,
    RedirectDetailSerializer,
    VersionSerializer,
    VersionUpdateSerializer,
)


class APIv3Settings:

    """
    Django REST Framework settings for APIv3.

    Override global DRF settings for APIv3 in particular. All ViewSet should
    inherit from this class to share/apply the same settings all over the APIv3.

    .. note::

        The only settings used from ``settings.REST_FRAMEWORK`` is
        ``DEFAULT_THROTTLE_RATES`` since it's not possible to define here.
    """

    # Using only ``TokenAuthentication`` for now, so we can give access to
    # specific carefully selected users only
    authentication_classes = (TokenAuthentication,)
    permission_classes = (PublicDetailPrivateListing,)

    pagination_class = LimitOffsetPagination
    LimitOffsetPagination.default_limit = 10

    renderer_classes = (AlphabeticalSortedJSONRenderer, BrowsableAPIRenderer)
    throttle_classes = (UserRateThrottle, AnonRateThrottle)
    filter_backends = (filters.DjangoFilterBackend,)
    metadata_class = SimpleMetadata


class ProjectsViewSet(APIv3Settings, NestedViewSetMixin, ProjectQuerySetMixin,
                      FlexFieldsMixin, CreateModelMixin, ReadOnlyModelViewSet):

    # Markdown docstring is automatically rendered by BrowsableAPIRenderer.

    """
    Endpoints related to ``Project`` objects.

    * Listing objects.
    * Detailed object.

    Retrieving only needed data using ``?fields=`` URL attribute is allowed.
    On the other hand, you can use ``?omit=`` and list the fields you want to skip in the response.

    ### Filters

    Allowed via URL attributes:

    * slug
    * slug__contains
    * name
    * name__contains

    ### Expandable fields

    There are some fields that are not returned by default because they are
    expensive to calculate. Although, they are available for those cases where
    they are needed.

    Allowed via ``?expand=`` URL attribue:

    * users
    * active_versions
    * active_versions.last_build
    * active_versions.last_build.confg


    ### Examples:

    * List my projects: ``/api/v3/projects/``
    * List my projects with offset and limit: ``/api/v3/projects/?offset=10&limit=25``
    * Filter list: ``/api/v3/projects/?name__contains=test``
    * Retrieve only needed data: ``/api/v3/projects/?fields=slug,created``
    * Retrieve specific project: ``/api/v3/projects/{project_slug}/``
    * Expand required fields: ``/api/v3/projects/{project_slug}/?expand=active_versions``
    * Translations of a project: ``/api/v3/projects/{project_slug}/translations/``
    * Subprojects of a project: ``/api/v3/projects/{project_slug}/subprojects/``
    * Superproject of a project: ``/api/v3/projects/{project_slug}/superproject/``

    Go to [https://docs.readthedocs.io/page/api/v3.html](https://docs.readthedocs.io/page/api/v3.html)
    for a complete documentation of the APIv3.
    """  # noqa

    model = Project
    lookup_field = 'slug'
    lookup_url_kwarg = 'project_slug'
    filterset_class = ProjectFilter
    queryset = Project.objects.all()
    permit_list_expands = [
        'active_versions',
        'active_versions.last_build',
        'active_versions.last_build.config',
    ]

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action.

        For GET it returns a serializer with many fields and on PUT/PATCH/POST,
        it return a serializer to validate just a few fields.
        """
        if self.action in ('list', 'retrieve', 'superproject'):
            return ProjectSerializer
        elif self.action in ('create',):
            return ProjectCreateSerializer
        # elif self.action in ('update', 'partial_update'):
        #     return ProjectUpdateSerializer

    def get_queryset(self):
        # Allow hitting ``/api/v3/projects/`` to list their own projects
        if self.basename == 'projects' and self.action == 'list':
            # We force returning ``Project`` objects here because it's under the
            # ``projects`` view.
            return self.admin_projects(self.request.user)

        # This could be a class attribute and managed on the ``ProjectQuerySetMixin`` in
        # case we want to extend the ``prefetch_related`` to other views as
        # well.
        queryset = super().get_queryset()
        return queryset.prefetch_related(
            'related_projects',
            'domains',
            'tags',
            'users',
        )

    def get_view_description(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        Make valid links for the user's documentation browseable API.

        If the user has already one project, we pick the first and make all the
        links for that project. Otherwise, we default to the placeholder.
        """
        description = super().get_view_description(*args, **kwargs)

        project = None
        if self.request and self.request.user.is_authenticated():
            project = self.request.user.projects.first()
            if project:
                # TODO: make the links clickable when ``kwargs.html=True``
                return mark_safe(description.format(project_slug=project.slug))
        return description

    def create(self, request, *args, **kwargs):
        """
        Override method to importing a Project.

        * Save the Project object
        * Assign the user from the request as owner
        * Sent project_import signal
        * Trigger an initial Build
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        headers = self.get_success_headers(serializer.data)

        # TODO: these lines need to be adapted for Corporate
        project.users.add(request.user)
        project_import.send(sender=project, request=request)
        trigger_initial_build(project, request.user)

        # Full render Project
        serializer = ProjectSerializer(instance=project)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=True, methods=['get'])
    def superproject(self, request, project_slug):
        """Return the superproject of a ``Project``."""
        project = self.get_object()
        try:
            superproject = project.superprojects.first().parent
            data = self.get_serializer(superproject).data
            return Response(data)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class SubprojectRelationshipViewSet(APIv3Settings, NestedViewSetMixin,
                                    ProjectQuerySetMixin, FlexFieldsMixin,
                                    ListModelMixin, GenericViewSet):

    # Markdown docstring exposed at BrowsableAPIRenderer.

    """List subprojects of a ``Project``."""

    # Private/Internal docstring

    """
    The main query is done via the ``NestedViewSetMixin`` using the
    ``parents_query_lookups`` defined when registering the urls.
    """  # noqa

    model = Project
    lookup_field = 'slug'
    lookup_url_kwarg = 'project_slug'
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()


class TranslationRelationshipViewSet(APIv3Settings, NestedViewSetMixin,
                                     ProjectQuerySetMixin, FlexFieldsMixin,
                                     ListModelMixin, GenericViewSet):

    # Markdown docstring exposed at BrowsableAPIRenderer.

    """List translations of a ``Project``."""

    # Private/Internal docstring
    """
    The main query is done via the ``NestedViewSetMixin`` using the
    ``parents_query_lookups`` defined when registering the urls.
    """  # noqa

    model = Project
    lookup_field = 'slug'
    lookup_url_kwarg = 'project_slug'
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()


# Inherit order is important here. ``NestedViewSetMixin`` has to be on the left
# of ``ProjectQuerySetMixin`` to make calling ``super().get_queryset()`` work
# properly and filter nested dependencies
class VersionsViewSet(APIv3Settings, NestedViewSetMixin, ProjectQuerySetMixin,
                      FlexFieldsMixin, UpdateModelMixin, ReadOnlyModelViewSet):

    model = Version
    lookup_field = 'slug'
    lookup_url_kwarg = 'version_slug'

    # Allow ``.`` (dots) on version slug
    lookup_value_regex = r'[^/]+'

    filterset_class = VersionFilter
    queryset = Version.objects.all()
    permit_list_expands = [
        'last_build',
        'last_build.config',
    ]

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action.

        For GET it returns a serializer with many fields and on PUT/PATCH/POST,
        it return a serializer to validate just a few fields.
        """
        if self.action in ('list', 'retrieve'):
            return VersionSerializer
        return VersionUpdateSerializer

    def update(self, request, *args, **kwargs):
        """
        Make PUT/PATCH behaves in the same way.

        Force to return 204 is the update was good.
        """

        # NOTE: ``Authorization:`` header is mandatory to use this method from
        # Browsable API since SessionAuthentication can't be used because we set
        # ``httpOnly`` on our cookies and the ``PUT/PATCH`` method are triggered
        # via Javascript
        super().update(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BuildsViewSet(APIv3Settings, NestedViewSetMixin, ProjectQuerySetMixin,
                    FlexFieldsMixin, ReadOnlyModelViewSet):
    model = Build
    lookup_field = 'pk'
    lookup_url_kwarg = 'build_pk'
    serializer_class = BuildSerializer
    filterset_class = BuildFilter
    queryset = Build.objects.all()
    permit_list_expands = [
        'config',
    ]


class BuildsCreateViewSet(BuildsViewSet, CreateModelMixin):

    def get_serializer_class(self):
        if self.action == 'create':
            return BuildCreateSerializer

        return super().get_serializer_class()

    def create(self, request, **kwargs):  # pylint: disable=arguments-differ
        project = self._get_parent_project()
        version = self._get_parent_version()

        _, build = trigger_build(project, version=version)

        # TODO: refactor this to be a serializer
        # BuildTriggeredSerializer(build, project, version).data
        data = {
            'build': BuildSerializer(build).data,
            'project': ProjectSerializer(project).data,
            'version': VersionSerializer(build.version).data,
        }

        if build:
            data.update({'triggered': True})
            code = status.HTTP_202_ACCEPTED
        else:
            data.update({'triggered': False})
            code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=code)


class RedirectsViewSet(APIv3Settings, NestedViewSetMixin, ProjectQuerySetMixin,
                       FlexFieldsMixin, ModelViewSet):
    model = Redirect
    lookup_field = 'pk'
    lookup_url_kwarg = 'redirect_pk'
    queryset = Redirect.objects.all()
    permission_classes = (IsAuthenticated & IsProjectAdmin,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('project')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RedirectCreateSerializer
        return RedirectDetailSerializer

    def perform_create(self, serializer):
        # Inject the project from the URL into the serializer
        serializer.validated_data.update({
            'project': self._get_parent_project(),
        })
        serializer.save()
