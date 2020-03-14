"""Queryset for the redirects app."""

import logging

from django.db import models
from django.db.models import Value, CharField, Q, F

from readthedocs.core.utils.extend import SettingsOverrideObject

log = logging.getLogger(__name__)


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

    def get_redirect_path_with_status(self, path, full_path=None, language=None, version_slug=None):
        # add extra fields with the ``path`` and ``full_path`` to perform a
        # filter at db level instead with Python
        queryset = self.annotate(
            path=Value(
                path,
                output_field=CharField(),
            ),
            full_path=Value(
                full_path,
                output_field=CharField(),
            ),
        )
        prefix = Q(
            redirect_type='prefix',
            path__startswith=F('from_url'),
        )
        page = Q(
            redirect_type='page',
            path__iexact=F('from_url'),
        )
        exact = (
            Q(
                redirect_type='exact',
                from_url__endswith='$rest',
                full_path__startswith=F('from_url_without_rest'),
            ) | Q(
                redirect_type='exact',
                full_path__iexact=F('from_url'),
            )
        )
        sphinx_html = (
            Q(
                redirect_type='sphinx_html',
                path__endswith='/',
            ) | Q(
                redirect_type='sphinx_html',
                path__endswith='/index.html',
            )
        )
        sphinx_htmldir = Q(
            redirect_type='sphinx_htmldir',
            path__endswith='.html',
        )

        queryset = queryset.filter(prefix | page | exact | sphinx_html | sphinx_htmldir)

        # There should be one and only one redirect returned by this query. I
        # can't think in a case where there can be more at this point. I'm
        # leaving the loop just in case for now
        for redirect in queryset.select_related('project'):
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
