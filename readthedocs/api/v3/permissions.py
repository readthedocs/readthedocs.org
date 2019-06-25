from rest_framework.permissions import IsAuthenticated


class PublicDetailPrivateListing(IsAuthenticated):

    """
    Permission class for our custom use case.

    * Always give permission for a ``detail`` request
    * Only give permission for ``listing`` request if user is admin of the project
    * Allow access to ``/projects`` (user's projects listing)
    """

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if is_authenticated:
            if view.basename == 'projects' and any([
                    view.action == 'list',
                    view.action == 'create',  # used to create Form in BrowsableAPIRenderer
                    view.action is None,  # needed for BrowsableAPIRenderer
            ]):
                # hitting ``/projects/``, allowing
                return True

            if view.detail:
                return True

            project = view._get_parent_project()
            if view.has_admin_permission(request.user, project):
                return True

        return False
