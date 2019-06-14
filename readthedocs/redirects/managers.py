# -*- coding: utf-8 -*-

"""Manager and queryset for the redirects app."""

from django.db.models import Manager
from django.db.models.query import QuerySet


class RedirectQuerySet(QuerySet):

    def get_redirect_path_with_status(self, path, language=None, version_slug=None):
        for redirect in self.select_related('project'):
            new_path = redirect.get_redirect_path(
                path=path,
                language=language,
                version_slug=version_slug,
            )
            if new_path:
                return new_path, redirect.http_status
        return (None, None)


RedirectManager = Manager.from_queryset(RedirectQuerySet)
