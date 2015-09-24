from django.db.models import Manager
from django.db.models.query import QuerySet


class RedirectQuerySet(QuerySet):
    def get_redirect_path(self, path, project, version=None):
        for redirect in self.select_related('project'):
            new_path = redirect.get_redirect_path(
                path=path, project=project, version=version)
            if new_path:
                return new_path


RedirectManager = Manager.from_queryset(RedirectQuerySet)
