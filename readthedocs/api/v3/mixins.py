from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class NestedParentObjectMixin:

    # Lookup names defined on ``readthedocs/api/v3/urls.py`` when defining the
    # mapping between URLs and views through the router.
    PROJECT_LOOKUP_NAMES = [
        'project__slug',
        'projects__slug',
        'superprojects__parent__slug',
        'main_language_project__slug',
    ]

    VERSION_LOOKUP_NAMES = [
        'version__slug',
    ]

    def _get_parent_object_lookup(self, lookup_names):
        query_dict = self.get_parents_query_dict()
        for lookup in lookup_names:
            value = query_dict.get(lookup)
            if value:
                return value

    def _get_parent_project(self):
        slug = self._get_parent_object_lookup(self.PROJECT_LOOKUP_NAMES)

        # when hitting ``/projects/<slug>/`` we don't have a "parent" project
        # because this endpoint is the base one, so we just get the project from
        # ``project_slug`` kwargs
        slug = slug or self.kwargs.get('project_slug')

        return get_object_or_404(Project, slug=slug)

    def _get_parent_version(self):
        project_slug = self._get_parent_object_lookup(self.PROJECT_LOOKUP_NAMES)
        slug = self._get_parent_object_lookup(self.VERSION_LOOKUP_NAMES)
        return get_object_or_404(
            Version,
            slug=slug,
            project__slug=project_slug,
        )


class ProjectQuerySetMixin(NestedParentObjectMixin):

    """
    Mixin to define queryset permissions for ViewSet only in one place.

    All APIv3 ViewSet should inherit this mixin, unless specific permissions
    required. In that case, a specific mixin for that case should be defined.
    """

    def detail_objects(self, queryset, user):
        # Filter results by user
        return queryset.api(user=user)

    def listing_objects(self, queryset, user):
        project = self._get_parent_project()
        if self.has_admin_permission(user, project):
            return queryset

        return queryset.none()

    def has_admin_permission(self, user, project):
        # Use .only for small optimization
        admin_projects = self.admin_projects(user).only('id')

        if project in admin_projects:
            return True

        return False

    def admin_projects(self, user):
        return Project.objects.for_admin_user(user=user)

    def get_queryset(self):
        """
        Filter results based on user permissions.

        1. returns ``Projects`` where the user is admin if ``/projects/`` is hit
        2. filters by parent ``project_slug`` (NestedViewSetMixin)
        2. returns ``detail_objects`` results if it's a detail view
        3. returns ``listing_objects`` results if it's a listing view
        4. raise a ``NotFound`` exception otherwise
        """

        # We need to have defined the class attribute as ``queryset = Model.objects.all()``
        queryset = super().get_queryset()

        # Detail requests are public
        if self.detail:
            return self.detail_objects(queryset, self.request.user)

        # List view are only allowed if user is owner of parent project
        return self.listing_objects(queryset, self.request.user)


class UpdatePartialUpdateMixin:
    """
    Make PUT/PATCH behaves in the same way.

    Force to return 204 if the update was good.
    """

    def update(self, request, *args, **kwargs):
        # NOTE: ``Authorization:`` header is mandatory to use this method from
        # Browsable API since SessionAuthentication can't be used because we set
        # ``httpOnly`` on our cookies and the ``PUT/PATCH`` method are triggered
        # via Javascript
        super().update(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)
