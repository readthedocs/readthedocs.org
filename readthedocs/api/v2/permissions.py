"""Defines access permissions for the API."""

from rest_framework import permissions

from readthedocs.builds.models import Version
from readthedocs.core.permissions import AdminPermission


class IsOwner(permissions.BasePermission):

    """Custom permission to only allow owners of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet
        return request.user in obj.users.all()


class CommentModeratorOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True  # TODO: Similar logic to #1084
        return AdminPermission.is_admin(request.user, obj.node.project)


class RelatedProjectIsOwner(permissions.BasePermission):

    """Custom permission to only allow owners of an object to edit it."""

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet
        return (
            request.method in permissions.SAFE_METHODS or
            (request.user in obj.project.users.all())
        )


class APIPermission(permissions.IsAuthenticatedOrReadOnly):

    """
    Control users access to the API.

    This permission should allow authenticated users readonly access to the API,
    and allow admin users write access. This should be used on API resources
    that need to implement write operations to resources that were based on the
    ReadOnlyViewSet
    """

    def has_permission(self, request, view):
        has_perm = super().has_permission(request, view)
        return has_perm or (request.user and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        has_perm = super().has_object_permission(
            request,
            view,
            obj,
        )
        return has_perm or (request.user and request.user.is_staff)


class APIRestrictedPermission(permissions.BasePermission):

    """
    Allow admin write, authenticated and anonymous read only.

    This differs from :py:class:`APIPermission` by not allowing for
    authenticated POSTs. This permission is endpoints like ``/api/v2/build/``,
    which are used by admin users to coordinate build instance creation, but
    only should be readable by end users.
    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS or
            (request.user and request.user.is_staff)
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS or
            (request.user and request.user.is_staff)
        )


class IsAuthorizedToViewVersion(permissions.BasePermission):

    """
    Checks if the user from the request has permissions to see the version.

    This permission class used in the FooterHTML and PageSearchAPIView views.

    .. note::

       Views using this permissions should implement the
       `_get_version` and `_get_project` methods.
    """

    def has_permission(self, request, view):
        project = view._get_project()
        version = view._get_version()
        has_access = (
            Version.objects
            .public(
                user=request.user,
                project=project,
                only_active=False,
            )
            .filter(pk=version.pk)
            .exists()
        )
        return has_access
