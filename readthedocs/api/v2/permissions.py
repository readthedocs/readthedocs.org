"""Defines access permissions for the API."""

from rest_framework import permissions
from rest_framework_api_key.permissions import BaseHasAPIKey
from rest_framework_api_key.permissions import KeyParser

from readthedocs.api.v2.models import BuildAPIKey


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

    This permission class used in PageSearchAPIView views.

    .. note::

       Views using this permissions should implement the
       `_get_version` and `_get_project` methods.
    """

    def has_permission(self, request, view):
        project = view._get_project()
        version = view._get_version()
        has_access = (
            version.is_public
            or project.versions.public(
                user=request.user,
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


class _BuildAPIKeyPermissionBase(BaseHasAPIKey):
    """
    Base class for BuildAPIKey permission classes.

    Validates the token, then — only when the key's scope matches —
    hangs the key on ``request.build_api_key`` for the viewset to
    read. Subclasses gate access by scope: project-scoped
    (``build_id is None``) or build-scoped (``build_id is not None``).

    A False return NEVER mutates ``request.build_api_key``. False
    means "not my scope, defer to the next class in the OR chain,"
    and downstream code that reads ``request.build_api_key`` should
    only ever see keys that actually earned view access.

    Consequence for ``ProjectViewSet``: a build-scoped key needs to
    GET the project (to pull ``clone_token`` for the sparse clone),
    so its permission chain composes ``HasBuildScopedBuildAPIKey &
    ReadOnlyPermission`` — the build-scoped class attaches the key
    on its own True branch. Don't rely on another class's False
    branch to attach it for you.

    A private ``_validated_build_api_key`` attribute is cached on the
    request so a second ``_BuildAPIKeyPermissionBase`` subclass in
    the same OR chain doesn't re-hit the DB to re-validate the same
    token.
    """

    model = BuildAPIKey
    key_parser = TokenKeyParser()

    def has_permission(self, request, view):
        # Downstream code (viewsets, serializer selection) reads
        # ``request.build_api_key`` unconditionally; make sure it's
        # defined even when no key is supplied or scope doesn't match.
        if not hasattr(request, "build_api_key"):
            request.build_api_key = None

        api_key = getattr(request, "_validated_build_api_key", None)
        if api_key is None:
            key = self.get_key(request)
            if not key:
                return False
            try:
                api_key = self.model.objects.get_from_key(key)
            except self.model.DoesNotExist:
                return False
            if api_key.has_expired:
                return False
            request._validated_build_api_key = api_key

        if not self._matches_scope(api_key):
            return False

        request.build_api_key = api_key
        return True

    def _matches_scope(self, api_key):
        raise NotImplementedError


class HasProjectScopedBuildAPIKey(_BuildAPIKeyPermissionBase):
    """
    Grants access to project-scoped BuildAPIKeys (``build_id is None``).

    Used everywhere the current API needs project-wide read+write from
    the builder — legacy ``update_docs_task`` path, webhooks, etc.
    """

    def _matches_scope(self, api_key):
        return api_key.build_id is None


class HasBuildScopedBuildAPIKey(_BuildAPIKeyPermissionBase):
    """
    Grants access to build-scoped BuildAPIKeys (``build_id is not None``).

    Used by the isolated-builders dispatcher path. Writes are further
    narrowed to that specific Build (and its Version, commands,
    notifications) by each viewset's ``get_queryset_for_api_key``.
    """

    def _matches_scope(self, api_key):
        return api_key.build_id is not None
