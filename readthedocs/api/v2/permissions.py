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


class ReadOnlyPermission(permissions.BasePermission):

    """Allow read-only access to authenticated and anonymous users."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


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

        # I had to add this condition here because I want to return a 400 when
        # the `project-slug` or `version-slug` are not sent to the API
        # endpoint. In those cases, we don't have a Project/Version and this
        # function was failing.
        #
        # I think it's a valid use case when Project/Version is invalid to be
        # able to return a good response from the API view.
        if project is None or version is None:
            return True

        has_access = (
            Version.objects.public(
                user=request.user,
                project=project,
                only_active=False,
            )
            .filter(pk=version.pk)
            .exists()
        )
        return has_access


class TokenKeyParser(KeyParser):

    """
    Custom key parser to use ``Token {TOKEN}`` as format.

    This is the same format we use in API V3 for auth/authz.
    """

    keyword = "Token"


class HasBuildAPIKey(BaseHasAPIKey):

    """
    Custom permission to inject the build API key into the request.

    We completely override the ``has_permission`` method
    to avoid having to parse and validate the key again on each view.
    The key is injected in the ``request.build_api_key`` attribute
    only if it's valid, otherwise it's set to ``None``.

    This grants read and write access to the API.
    """

    model = BuildAPIKey
    key_parser = TokenKeyParser()

    def has_permission(self, request, view):
        request.build_api_key = None
        key = self.get_key(request)
        if not key:
            return False

        try:
            build_api_key = self.model.objects.get_from_key(key)
        except self.model.DoesNotExist:
            return False

        if build_api_key.has_expired:
            return False

        request.build_api_key = build_api_key
        return True
