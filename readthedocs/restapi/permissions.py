from rest_framework import permissions
from privacy.backend import AdminPermission


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet
        return request.user in obj.users.all()


class CommentModeratorOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, comment):
        if request.method in permissions.SAFE_METHODS:
            return True  # TODO: Similar logic to #1084
        else:
            return AdminPermission.is_admin(request.user, comment.node.project)


class RelatedProjectIsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet
        return request.user in obj.project.users.all()


class APIPermission(permissions.IsAuthenticatedOrReadOnly):
    '''
    This permission should allow authenicated users readonly access to the API,
    and allow admin users write access. This should be used on API resources
    that need to implement write operations to resources that were based on the
    ReadOnlyViewSet
    '''

    def has_object_permission(self, request, view, obj):
        has_perm = super(APIPermission, self).has_object_permission(
            request, view, obj)
        return has_perm or (request.user and request.user.is_staff)



