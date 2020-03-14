"""Queryset for the redirects app."""

import logging

from django.db import models, DataError
from django.db.models import Value, CharField, IntegerField, Q, F, ExpressionWrapper
from django.db.models.functions import Substr, Length

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

            from_url_length=ExpressionWrapper(
                Length('from_url'),
                output_field=IntegerField(),
            ),

            # 1-indexed
            from_url_without_rest=Substr(
                'from_url',
                1,
                F('from_url_length') - 5,  # Strip "$rest"
                output_field=CharField(),
            ),

            # 1-indexed
            full_path_without_rest=Substr(
                'full_path',
                1,
                F('from_url_length') - 5,  # Strip "$rest"
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
                # This works around a bug in Django doing a substr and an endswith,
                # so instead we do 2 substrs and an exact
                # https://code.djangoproject.com/ticket/29155
                full_path_without_rest=F('from_url_without_rest'),
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

        try:
            # Using the ``exact`` Q object we created here could cause an
            # execption because it uses ``from_url_without_rest`` and
            # ``full_path_without_rest`` which could produce a database error
            # ("negative substring length not allowed") when ``from_url``'s
            # length is less than 5 ('$rest' string substracted from it). We
            # perform a query using ``exact`` here and if it fail we catch it
            # and just ignore these redirects for this project.
            queryset = queryset.filter(prefix | page | exact | sphinx_html | sphinx_htmldir)
            queryset.select_related('project').count()
        except DataError:
            # Fallback to the query without using ``exact`` on it
            log.warning('Failing Exact Redirects on this project. Ignoring them.')
            queryset = queryset.filter(prefix | page | sphinx_html | sphinx_htmldir)

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
