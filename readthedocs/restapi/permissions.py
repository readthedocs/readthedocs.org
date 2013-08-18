from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet
        import ipdb; ipdb.set_trace()
        return request.user in obj.users.all() 

class RelatedProjectIsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet
        import ipdb; ipdb.set_trace()
        return request.user in obj.project.users.all() 