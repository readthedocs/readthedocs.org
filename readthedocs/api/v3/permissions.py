from rest_framework.permissions import BasePermission

from readthedocs.api.v3.models import RTDAPIKey
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


class HasAPIKeyPermission(BasePermission):
    """
    Grant permission if the request was authenticated with an API key that has the required permission.

    Views using this permission should define the ``api_key_permission`` attribute.
    Checking that the key has access to the object being accessed is up to the view.
    """

    def has_permission(self, request, view):
        api_key = request.auth
        return isinstance(api_key, RTDAPIKey) and api_key.has_permission(view.api_key_permission)
