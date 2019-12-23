from rest_framework.permissions import IsAuthenticated, BasePermission

from readthedocs.core.utils.extend import SettingsOverrideObject


class UserProjectsListing(BasePermission):
    """Allow access to ``/projects`` (user's projects listing)."""

    def has_permission(self, request, view):
        if view.basename == 'projects' and any([
                view.action == 'list',
                view.action == 'create',  # used to create Form in BrowsableAPIRenderer
                view.action is None,  # needed for BrowsableAPIRenderer
        ]):
            # hitting ``/projects/``, allowing
            return True


class PublicDetailPrivateListing(IsAuthenticated):

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
        if view.detail and view.action in ('list', 'retrieve', 'superproject'):
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


class CommonPermissionsBase(BasePermission):

    """
    Common permission class used for most APIv3 endpoints.

    This class should be used by ``APIv3Settings.permission_classes`` to define
    the permissions for most APIv3 endpoints. It has to be overriden from
    corporate to define proper permissions there.
    """

    def has_permission(self, request, view):
        if not IsAuthenticated().has_permission(request, view):
            return False

        return any([
            UserProjectsListing().has_permission(request, view),
            PublicDetailPrivateListing().has_permission(request, view),
        ])


class CommonPermissions(SettingsOverrideObject):
    _default_class = CommonPermissionsBase
