"""Queryset for the redirects app."""
from urllib.parse import urlparse

import structlog
from django.db import models
from django.db.models import CharField, F, Q, Value

from readthedocs.core.permissions import AdminPermission

log = structlog.get_logger(__name__)


class RedirectQuerySet(models.QuerySet):

    """Redirects take into account their own privacy_level setting."""

    use_for_related_fields = True

    def _add_from_user_projects(self, queryset, user):
        if user.is_authenticated:
            projects_pk = (
                AdminPermission.projects(
                    user=user,
                    admin=True,
                    member=True,
                )
                .values_list('pk', flat=True)
            )
            user_queryset = self.filter(project__in=projects_pk)
            queryset = user_queryset | queryset
        return queryset.distinct()

    def api(self, user=None):
        queryset = self.none()
        if user:
            queryset = self._add_from_user_projects(queryset, user)
        return queryset

    def get_redirect_path_with_status(
        self, path, full_path=None, language=None, version_slug=None, forced_only=False
    ):
        """
        Get the final redirect with its status code.

        :param path: Is the path without the language and version parts.
        :param full_path: Is the full path including the language and version parts.
        :param forced_only: Include only forced redirects in the results.
        """
        # Small optimization to skip executing the big query below.
        if forced_only and not self.filter(force=True).exists():
            return None, None

        normalized_path = self._normalize_path(path)
        normalized_full_path = self._normalize_path(full_path)

        # add extra fields with the ``path`` and ``full_path`` to perform a
        # filter at db level instead with Python.
        queryset = self.annotate(
            path=Value(
                normalized_path,
                output_field=CharField(),
            ),
            full_path=Value(
                normalized_full_path,
                output_field=CharField(),
            ),
        )
        prefix = Q(
            redirect_type='prefix',
            path__startswith=F('from_url'),
        )
        page = Q(
            redirect_type='page',
            path__exact=F('from_url'),
        )
        exact = (
            Q(
                redirect_type='exact',
                from_url__endswith='$rest',
                full_path__startswith=F('from_url_without_rest'),
            ) | Q(
                redirect_type='exact',
                full_path__exact=F('from_url'),
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
        if forced_only:
            queryset = queryset.filter(force=True)

        # There should be one and only one redirect returned by this query. I
        # can't think in a case where there can be more at this point. I'm
        # leaving the loop just in case for now
        for redirect in queryset.select_related('project'):
            new_path = redirect.get_redirect_path(
                path=normalized_path,
                language=language,
                version_slug=version_slug,
            )
            if new_path:
                return new_path, redirect.http_status
        return (None, None)

    def _normalize_path(self, path):
        r"""
        Normalize path.

        We normalize ``path`` to:

        - Remove the query params.
        - Remove any invalid URL chars (\r, \n, \t).
        - Always start the path with ``/``.

        We don't use ``.path`` to avoid parsing the filename as a full url.
        For example if the path is ``http://example.com/my-path``,
        ``.path`` would return ``my-path``.
        """
        parsed_path = urlparse(path)
        normalized_path = parsed_path._replace(query="").geturl()
        normalized_path = "/" + normalized_path.lstrip("/")
        return normalized_path
