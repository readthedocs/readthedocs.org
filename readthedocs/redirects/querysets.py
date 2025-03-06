"""Queryset for the redirects app."""

from urllib.parse import urlparse

import structlog
from django.db import models
from django.db.models import CharField
from django.db.models import F
from django.db.models import Q
from django.db.models import Value

from readthedocs.core.permissions import AdminPermission
from readthedocs.core.querysets import NoReprQuerySet
from readthedocs.redirects.constants import CLEAN_URL_TO_HTML_REDIRECT
from readthedocs.redirects.constants import EXACT_REDIRECT
from readthedocs.redirects.constants import HTML_TO_CLEAN_URL_REDIRECT
from readthedocs.redirects.constants import PAGE_REDIRECT


log = structlog.get_logger(__name__)


class RedirectQuerySet(NoReprQuerySet, models.QuerySet):
    """Redirects take into account their own privacy_level setting."""

    use_for_related_fields = True

    def _add_from_user_projects(self, queryset, user):
        if user.is_authenticated:
            projects_pk = AdminPermission.projects(
                user=user,
                admin=True,
                member=True,
            ).values_list("pk", flat=True)
            user_queryset = self.filter(project__in=projects_pk)
            queryset = user_queryset | queryset
        return queryset.distinct()

    def api(self, user=None):
        queryset = self.none()
        if user:
            queryset = self._add_from_user_projects(queryset, user)
        return queryset

    def api_v2(self, *args, **kwargs):
        # API v2 is the same as API v3 for .org, but it's
        # different for .com, this method is overridden there.
        return self.api(*args, **kwargs)

    def get_matching_redirect_with_path(
        self, filename, path=None, language=None, version_slug=None, forced_only=False
    ):
        """
        Get the matching redirect with the path to redirect to.

        :param filename: The filename being served.
        :param path: The whole path from the request.
        :param forced_only: Include only forced redirects in the results.
        :returns: A tuple with the matching redirect and new path.
        """
        # Small optimization to skip executing the big query below.
        # TODO: use filter(enabled=True) once we have removed the null option from the field.
        if forced_only and not self.filter(force=True).exclude(enabled=False).exists():
            return None, None

        normalized_filename = self._normalize_path(filename)
        normalized_path = self._normalize_path(path)

        # Useful to allow redirects to match paths with or without trailling slash.
        # For example, ``/docs`` will match ``/docs/`` and ``/docs``.
        filename_without_trailling_slash = self._strip_trailling_slash(normalized_filename)
        path_without_trailling_slash = self._strip_trailling_slash(normalized_path)

        # Add extra fields with the ``filename`` and ``path`` to perform a
        # filter at db level instead with Python.
        queryset = self.annotate(
            filename=Value(
                filename,
                output_field=CharField(),
            ),
            path=Value(
                normalized_path,
                output_field=CharField(),
            ),
            filename_without_trailling_slash=Value(
                filename_without_trailling_slash,
                output_field=CharField(),
            ),
            path_without_trailling_slash=Value(
                path_without_trailling_slash,
                output_field=CharField(),
            ),
        )
        page = Q(
            redirect_type=PAGE_REDIRECT,
            from_url_without_rest__isnull=True,
            filename_without_trailling_slash__exact=F("from_url"),
        ) | Q(
            redirect_type=PAGE_REDIRECT,
            from_url_without_rest__isnull=False,
            filename__startswith=F("from_url_without_rest"),
        )
        exact = Q(
            redirect_type=EXACT_REDIRECT,
            from_url_without_rest__isnull=True,
            path_without_trailling_slash__exact=F("from_url"),
        ) | Q(
            redirect_type=EXACT_REDIRECT,
            from_url_without_rest__isnull=False,
            path__startswith=F("from_url_without_rest"),
        )
        clean_url_to_html = Q(redirect_type=CLEAN_URL_TO_HTML_REDIRECT)
        html_to_clean_url = Q(redirect_type=HTML_TO_CLEAN_URL_REDIRECT)

        if filename in ["/index.html", "/"]:
            # If the filename is a root index file (``/index.html`` or ``/``), we only need to match page and exact redirects,
            # since we don't have a filename to redirect to for clean_url_to_html and html_to_clean_url redirects.
            queryset = queryset.filter(page | exact)
        elif filename:
            if filename.endswith(("/index.html", "/")):
                queryset = queryset.filter(page | exact | clean_url_to_html)
            elif filename.endswith(".html"):
                queryset = queryset.filter(page | exact | html_to_clean_url)
            else:
                queryset = queryset.filter(page | exact)
        else:
            # If the filename is empty, we only need to match exact redirects.
            # Since the other types of redirects are not valid without a filename.
            queryset = queryset.filter(exact)

        # TODO: use filter(enabled=True) once we have removed the null option from the field.
        queryset = queryset.exclude(enabled=False)
        if forced_only:
            queryset = queryset.filter(force=True)

        redirect = queryset.select_related("project").first()
        if redirect:
            new_path = redirect.get_redirect_path(
                filename=normalized_filename,
                path=normalized_path,
                language=language,
                version_slug=version_slug,
            )
            return redirect, new_path
        return None, None

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

    def _strip_trailling_slash(self, path):
        """Stripe the trailling slash from the path, making sure the root path is always ``/``."""
        path = path.rstrip("/")
        if path == "":
            return "/"
        return path
