from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.history import safe_update_change_reason
from readthedocs.core.history import set_change_reason
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project


class UpdateChangeReasonMixin:
    """
    Set the change_reason on the model changed through this API view.

    The view should inherit one of:

    - CreateModelMixin
    - UpdateModelMixin
    - DestroyModelMixin

    Unlike the original methods,
    these return the instance that was created/updated,
    so they are easy to override without having to save the object twice.
    """

    change_reason = None

    def get_change_reason(self):
        if self.change_reason:
            return self.change_reason
        klass = self.__class__.__name__
        return f"origin=api-v3 class={klass}"

    def perform_create(self, serializer):
        obj = serializer.save()
        safe_update_change_reason(obj, self.get_change_reason())
        return obj

    def perform_update(self, serializer):
        set_change_reason(serializer.instance, self.get_change_reason())
        obj = serializer.save()
        return obj

    def perform_destroy(self, instance):
        set_change_reason(instance, self.get_change_reason())
        super().perform_destroy(instance)


class NestedParentObjectMixin:
    # Lookup names defined on ``readthedocs/api/v3/urls.py`` when defining the
    # mapping between URLs and views through the router.
    PROJECT_LOOKUP_NAMES = [
        "project__slug",
        "projects__slug",
        "parent__slug",
        "superprojects__parent__slug",
        "main_language_project__slug",
    ]

    VERSION_LOOKUP_NAMES = [
        "version__slug",
    ]

    ORGANIZATION_LOOKUP_NAMES = [
        "organization__slug",
        "organizations__slug",
    ]

    BUILD_LOOKUP_NAMES = [
        "build__id",
    ]

    USER_LOOKUP_NAMES = [
        "user__username",
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
        slug = slug or self.kwargs.get("project_slug")

        return get_object_or_404(Project, slug=slug)

    def _get_parent_build(self):
        """
        Filter the build by the permissions of the current user.

        Build permissions depend not only on the project, but also on
        the version, Build.objects.api takes all that into consideration.
        """
        project_slug = self._get_parent_object_lookup(self.PROJECT_LOOKUP_NAMES)
        build_pk = self._get_parent_object_lookup(self.BUILD_LOOKUP_NAMES)
        return get_object_or_404(
            Build.objects.api(user=self.request.user),
            pk=build_pk,
            project__slug=project_slug,
        )

    def _get_parent_version(self):
        project_slug = self._get_parent_object_lookup(self.PROJECT_LOOKUP_NAMES)
        slug = self._get_parent_object_lookup(self.VERSION_LOOKUP_NAMES)
        return get_object_or_404(
            Version,
            slug=slug,
            project__slug=project_slug,
        )

    def _get_parent_organization(self):
        slug = self._get_parent_object_lookup(self.ORGANIZATION_LOOKUP_NAMES)

        # when hitting ``/organizations/<slug>/`` we don't have a "parent" organization
        # because this endpoint is the base one, so we just get the organization from
        # ``organization_slug`` kwargs
        slug = slug or self.kwargs.get("organization_slug")

        return get_object_or_404(
            Organization,
            slug=slug,
        )

    def _get_parent_user(self):
        username = self._get_parent_object_lookup(self.USER_LOOKUP_NAMES)
        username = username or self.kwargs.get("user_username")

        return get_object_or_404(
            User,
            username=username,
        )


class ProjectQuerySetMixin(NestedParentObjectMixin):
    """
    Mixin to define queryset permissions for ViewSet only in one place.

    All APIv3 ViewSet should inherit this mixin, unless specific permissions
    required. In that case, a specific mixin for that case should be defined.

    .. note::

       When using nested views, the ``NestedViewSetMixin`` should be
       used and should be before this mixin in the inheritance list.
       So it can properly filter the queryset based on the parent object.
    """

    def has_admin_permission(self, user, project):
        # Use .only for small optimization
        admin_projects = self.admin_projects(user).only("id")

        if project in admin_projects:
            return True

        return False

    def admin_projects(self, user):
        return Project.objects.for_admin_user(user=user)

    def get_queryset(self):
        """Filter projects or related resources based on the permissions of the current user."""
        return self.model.objects.api(user=self.request.user)


class OrganizationQuerySetMixin(NestedParentObjectMixin):
    """
    Mixin to define queryset permissions for ViewSet only in one place.

    All APIv3 organizations' ViewSet should inherit this mixin, unless specific permissions
    required. In that case, a specific mixin for that case should be defined.

    .. note::

       When using nested views, the ``NestedViewSetMixin`` should be
       used and should be before this mixin in the inheritance list.
       So it can properly filter the queryset based on the parent object.
    """

    def has_admin_permission(self, user, organization):
        """Check if user is an owner of the organization."""
        if self.admin_organizations(user).filter(pk=organization.pk).exists():
            return True

        return False

    def is_admin_member(self, user, organization):
        """Check if user is an owner or belongs to a team with admin permissions of the organization."""
        if self.has_admin_permission(user, organization):
            return True

        return (
            Project.objects.for_admin_user(user=user)
            .filter(organizations__in=[organization])
            .exists()
        )

    def admin_organizations(self, user):
        return Organization.objects.for_admin_user(user=user)

    def get_queryset(self):
        """Filter organizations or related resources based on the permissions of the current user."""
        return self.model.objects.api(user=self.request.user)


class UserQuerySetMixin(NestedParentObjectMixin):
    """
    Mixin to define queryset permissions for ViewSet only in one place.

    All APIv3 user' ViewSet should inherit this mixin, unless specific permissions
    required. In that case, a specific mixin for that case should be defined.
    """

    def has_admin_permission(self, requesting_user, accessing_user):
        if requesting_user == accessing_user:
            return True

        return False


class UpdateMixin:
    """Make PUT to return 204 on success like PATCH does."""

    def update(self, request, *args, **kwargs):
        # NOTE: ``Authorization:`` header is mandatory to use this method from
        # Browsable API since SessionAuthentication can't be used because we set
        # ``httpOnly`` on our cookies and the ``PUT/PATCH`` method are triggered
        # via Javascript
        super().update(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RemoteQuerySetMixin:
    def get_queryset(self):
        return self.model.objects.api(self.request.user)
