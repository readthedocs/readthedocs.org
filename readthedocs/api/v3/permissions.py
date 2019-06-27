from rest_framework.permissions import BasePermission


class PublicDetailPrivateListing(BasePermission):

    """
    Permission class for our custom use case.

    * Always give permission for a ``detail`` request
    * Only give permission for ``listing`` request if user is admin of the project
    """

    def has_permission(self, request, view):
        if view.detail:
            return True

        project = view._get_parent_project()
        if view.has_admin_permission(request.user, project):
            return True


class ListCreateProject(BasePermission):

    """
    Permission class to grant projects listing and project creation.

    * Allow access to ``/projects`` (user's projects listing)
    """

    def has_permission(self, request, view):
        if view.basename == 'projects' and any([
                view.action == 'list',
                view.action == 'create',  # used to create Form in BrowsableAPIRenderer
                view.action is None,  # needed for BrowsableAPIRenderer
        ]):
            # hitting ``/projects/``, allowing
            return True
