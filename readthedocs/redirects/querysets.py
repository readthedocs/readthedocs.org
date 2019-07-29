"""Queryset for the redirects app."""

from django.db import models

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects import constants


class RedirectQuerySetBase(models.QuerySet):

    """Redirects take into account their own privacy_level setting."""

    use_for_related_fields = True

    def _add_user_repos(self, queryset, user):
        if user.is_authenticated:
            projects_pk = user.projects.all().values_list('pk', flat=True)
            user_queryset = self.filter(project__in=projects_pk)
            queryset = user_queryset | queryset
        return queryset.distinct()

    def api(self, user=None, detail=True):
        queryset = self.none()
        if user:
            queryset = self._add_user_repos(queryset, user)
        return queryset

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


class RedirectQuerySet(SettingsOverrideObject):
    _default_class = RedirectQuerySetBase
