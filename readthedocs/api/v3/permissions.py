from rest_framework.permissions import IsAuthenticated


class PublicDetailPrivateListing(IsAuthenticated):

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if is_authenticated:
            if view.basename == 'projects' and view.action == 'list':
                # hitting ``/projects/``, allowing
                return True

            if view.detail:
                return True

            project = view._get_parent_project()
            if view.has_admin_permission(request.user, project):
                return True

        return False
