from rest_framework.permissions import BasePermission, IsAuthenticated

from readthedocs.core.utils.extend import SettingsOverrideObject
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


class UserProjectsListing(BasePermission):

    """Allow access to ``/projects`` (user's projects listing)."""

    def has_permission(self, request, view):
        if view.basename == "projects" and view.action in (
            "list",
            "create",  # used to create Form in BrowsableAPIRenderer
            None,  # needed for BrowsableAPIRenderer
        ):
            # hitting ``/projects/``, allowing
            return True


class PublicDetailPrivateListing(BasePermission):

    """
    Permission class for our custom use case.

    * Always give permission for a ``detail`` request
    * Only give permission for ``listing`` request if user is admin of the project
    """

    def has_permission(self, request, view):
        # NOTE: ``superproject`` is an action name, defined by the class
        # method under ``ProjectViewSet``. We should apply the same
        # permissions restrictions than for a detail action (since it only
        # returns one superproject if exists). ``list`` and ``retrieve`` are
        # DRF standard action names (same as ``update`` or ``partial_update``).
        if view.detail and view.action in ("list", "retrieve", "superproject"):
            # detail view is only allowed on list/retrieve actions (not
            # ``update`` or ``partial_update``).
            return True

        project = view._get_parent_project()
        if view.has_admin_permission(request.user, project):
            return True

        return False


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


class UserOrganizationsListing(BasePermission):
    def has_permission(self, request, view):
        if view.basename == "organizations" and view.action in (
            "list",
            None,  # needed for BrowsableAPIRenderer
        ):
            # hitting ``/organizations/``, allowing
            return True


class CommonPermissionsBase(BasePermission):

    """
    Common permission class used for most APIv3 endpoints.

    This class should be used by ``APIv3Settings.permission_classes`` to define
    the permissions for most APIv3 endpoints. It has to be overridden from
    corporate to define proper permissions there.
    """

    def has_permission(self, request, view):
        if not IsAuthenticated().has_permission(request, view):
            return False

        return UserProjectsListing().has_permission(
            request, view
        ) or PublicDetailPrivateListing().has_permission(request, view)


class CommonPermissions(SettingsOverrideObject):
    _default_class = CommonPermissionsBase
