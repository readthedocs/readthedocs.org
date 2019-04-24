from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework_extensions.settings import extensions_api_settings

from readthedocs.projects.models import Project


class NestedParentProjectMixin:

    def get_parent_project(self):

        project_slug = None
        for kwarg_name, kwarg_value in self.kwargs.items():
            if kwarg_name.startswith(extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX) and 'project' in kwarg_name:
                project_slug = kwarg_value

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

        # List view are only allowed if user is owner
        if self.get_parent_project() in Project.objects.for_admin_user(user=self.request.user):
            return queryset

        raise PermissionDenied
