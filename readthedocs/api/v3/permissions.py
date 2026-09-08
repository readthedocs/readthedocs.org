from rest_framework.permissions import SAFE_METHODS
from rest_framework.permissions import BasePermission
from rest_framework_api_key.permissions import BaseHasAPIKey

from readthedocs.api.v2.models import ProjectAPIKey
from readthedocs.api.v2.permissions import TokenKeyParser
from readthedocs.api.v3.authentication import has_project_api_key_header
from readthedocs.subscriptions.constants import TYPE_EMBED_API
from readthedocs.subscriptions.products import get_feature


class HasEmbedAPIAccess(BasePermission):
    """
    Check if the project being accessed has access to the Embed API.

    The embedded API V3 allows getting content from external sites tha
    aren't attached to a project. Those sites are restricted to the ones
    from ``RTD_EMBED_API_EXTERNAL_DOMAINS``, so we just allow that.
    """

    message = (
        "Content embedding isn't available in your current plan. "
        "Upgrade your subscription to enable this feature. "
        "https://about.readthedocs.com/pricing/."
    )

    def has_permission(self, request, view):
        project = view._get_project()
        # The project is None when the is requesting a section from an external site.
        if project and not get_feature(project, feature_type=TYPE_EMBED_API):
            return False
        return True


class IsCurrentUser(BasePermission):
    """Grant permission if user is the same as the one being accessed."""

    def has_permission(self, request, view):
        user = view._get_parent_user()
        if user == request.user:
            return True


class IsProjectAdmin(BasePermission):
    """Grant permission if user has admin rights on the Project."""

    def has_permission(self, request, view):
        project = view._get_parent_project()
        if view.has_admin_permission(request.user, project):
            return True


class IsOrganizationAdmin(BasePermission):
    def has_permission(self, request, view):
        organization = view._get_parent_organization()
        if view.has_admin_permission(request.user, organization):
            return True


class IsOrganizationAdminMember(BasePermission):
    def has_permission(self, request, view):
        organization = view._get_parent_organization()
        if view.is_admin_member(request.user, organization):
            return True


class HasProjectAPIKey(BaseHasAPIKey):
    """
    Custom permission to inject the project API key into the request.

    The key is injected in the ``request.project_api_key`` attribute only if
    it's valid, otherwise it's set to ``None``. Read only keys are granted safe
    methods only.

    .. warning::

       ``ProjectQuerySetMixin.get_queryset`` relies on the attribute set here,
       and DRF only guarantees that the *leftmost* operand of an ``OR`` is
       evaluated. So this class always has to come first when combining
       permissions, like ``HasProjectAPIKey | ReadOnlyPermission``.
    """

    model = ProjectAPIKey
    key_parser = TokenKeyParser()

    def has_permission(self, request, view):
        request.project_api_key = None
        # Don't hit the database for user tokens.
        if not has_project_api_key_header(request):
            return False

        key = self.get_key(request)

        try:
            api_key = self.model.objects.get_from_key(key)
        except self.model.DoesNotExist:
            return False

        # Internal keys belong to the builders and are handled by
        # ``readthedocs.api.v2.permissions.HasInternalAPIKey``.
        if api_key.has_expired or api_key.internal:
            return False

        request.project_api_key = api_key

        if api_key.is_read_only:
            return request.method in SAFE_METHODS
        return True


class HasProjectAPIKeyForProject(HasProjectAPIKey):
    """Grant permission if the API key belongs to the project from the URL."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.project_api_key.project_id == view._get_parent_project().pk


class NoProjectAPIKey(BasePermission):
    """
    Grant permission if the request doesn't carry a project API key.

    Used to guard the permission classes that would otherwise let a key through
    on the endpoints anonymous users can read, so a key for the wrong project is
    rejected instead of silently returning an empty list.
    """

    def has_permission(self, request, view):
        return not has_project_api_key_header(request)
