"""Defines access permissions for the API."""

from rest_framework import permissions
from rest_framework_api_key.permissions import BaseHasAPIKey, KeyParser
from readthedocs.api.v2.models import BuildAPIKey

from readthedocs.builds.models import Version


class IsOwner(permissions.BasePermission):

    """Custom permission to only allow owners of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the snippet
        return request.user in obj.users.all()


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


class TokenKeyParser(KeyParser):
    keyword = "Token"


class HasBuildAPIKey(BaseHasAPIKey):
    model = BuildAPIKey
    key_parser = TokenKeyParser()

    def has_permission(self, request, view):
        build_api_key = None
        has_permission =  super().has_permission(request, view)
        if has_permission:
            key = self.get_key(request)
            build_api_key =  self.model.objects.get_from_key(key)
        request.build_api_key = build_api_key
        return has_permission
