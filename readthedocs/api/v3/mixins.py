from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from readthedocs.projects.models import Project


class NestedParentProjectMixin:

    # Lookup names defined on ``readthedocs/api/v3/urls.py`` when defining the
    # mapping between URLs and views through the router.
    LOOKUP_NAMES = [
        'project__slug',
        'projects__slug',
        'superprojects__parent__slug',
        'main_language_project__slug',
    ]

    def _get_parent_project(self):
        project_slug = None
        query_dict = self.get_parents_query_dict()
        for lookup in self.LOOKUP_NAMES:
            value = query_dict.get(lookup)
            if value:
                project_slug = value
                break

        return get_object_or_404(Project, slug=project_slug)


class APIAuthMixin(NestedParentProjectMixin):

    """
    Mixin to define queryset permissions for ViewSet only in one place.

    All APIv3 ViewSet should inherit this mixin, unless specific permissions
    required. In that case, an specific mixin for that case should be defined.
    """

    def get_queryset(self):
        """
        Filter results based on user permissions.

        1. filters by parent ``project_slug`` (NestedViewSetMixin).
        2. return those results if it's a detail view.
        3. if it's a list view, it checks if the user is admin of the parent
           object (project) and return the same results.
        4. raise a ``PermissionDenied`` exception if the user is not an admin.
        """

        # NOTE: ``super().get_queryset`` produces the filter by ``NestedViewSetMixin``
        # we need to have defined the class attribute as ``queryset = Model.objects.all()``
        queryset = super().get_queryset()

        # Filter results by user
        # NOTE: we don't override the manager in User model, so we don't have
        # ``.api`` method there
        if self.model is not User:
            queryset = queryset.api(user=self.request.user)

        # Detail requests are public
        if self.detail:
            return queryset

        allowed_projects = Project.objects.for_admin_user(user=self.request.user)

        # Allow hitting ``/api/v3/projects/`` to list their own projects
        if self.basename == 'projects' and self.action == 'list':
            return allowed_projects

        # List view are only allowed if user is owner of parent project
        project = self._get_parent_project()
        if project in allowed_projects:
            return queryset

        raise PermissionDenied
