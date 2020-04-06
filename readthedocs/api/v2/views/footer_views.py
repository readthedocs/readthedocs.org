"""Endpoint to generate footer HTML."""

import re

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import loader as template_loader
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jsonp.renderers import JSONPRenderer

from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.api.v2.signals import footer_response
from readthedocs.builds.constants import LATEST, TAG
from readthedocs.builds.models import Version
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.models import Project
from readthedocs.projects.version_handling import (
    highest_version,
    parse_version_failsafe,
)


def get_version_compare_data(project, base_version=None):
    """
    Retrieve metadata about the highest version available for this project.

    :param base_version: We assert whether or not the base_version is also the
                         highest version in the resulting "is_highest" value.
    """
    if not project.show_version_warning:
        return {'is_highest': False}

    versions_qs = (
        Version.internal.public(project=project)
        .filter(built=True, active=True)
    )

    # Take preferences over tags only if the project has at least one tag
    if versions_qs.filter(type=TAG).exists():
        versions_qs = versions_qs.filter(type=TAG)

    # Optimization
    versions_qs = versions_qs.select_related('project')

    highest_version_obj, highest_version_comparable = highest_version(
        versions_qs,
    )
    ret_val = {
        'project': str(highest_version_obj),
        'version': str(highest_version_comparable),
        'is_highest': True,
    }
    if highest_version_obj:
        # Never link to the dashboard,
        # users reading the docs may don't have access to the dashboard.
        ret_val['url'] = highest_version_obj.get_absolute_url()
        ret_val['slug'] = highest_version_obj.slug
    if base_version and base_version.slug != LATEST:
        try:
            base_version_comparable = parse_version_failsafe(
                base_version.verbose_name,
            )
            if base_version_comparable:
                # This is only place where is_highest can get set. All error
                # cases will be set to True, for non- standard versions.
                ret_val['is_highest'] = (
                    base_version_comparable >= highest_version_comparable
                )
            else:
                ret_val['is_highest'] = True
        except (Version.DoesNotExist, TypeError):
            ret_val['is_highest'] = True
    return ret_val


class BaseFooterHTML(APIView):

    """
    Render and return footer markup.

    .. note::

       The methods `_get_project` and `_get_version`
       are called many times, so a basic cache is implemented.
    """

    http_method_names = ['get']
    permission_classes = [IsAuthorizedToViewVersion]
    renderer_classes = [JSONRenderer, JSONPRenderer]

    def _get_project(self):
        cache_key = '_cached_project'
        project = getattr(self, cache_key, None)

        if not project:
            project_slug = self.request.GET.get('project', None)
            project = get_object_or_404(Project, slug=project_slug)
            setattr(self, cache_key, project)

        return project

    def _get_version(self):
        cache_key = '_cached_version'
        version = getattr(self, cache_key, None)

        if not version:
            version_slug = self.request.GET.get('version', None)

            # Hack in a fix for missing version slug deploy
            # that went out a while back
            if version_slug == '':
                version_slug = LATEST

            project = self._get_project()
            version = get_object_or_404(
                project.versions.all(),
                slug__iexact=version_slug,
            )
            setattr(self, cache_key, version)

        return version

    def _get_active_versions_sorted(self):
        """Get all versions that the user has access, sorted."""
        project = self._get_project()
        versions = project.ordered_active_versions(
            user=self.request.user,
        )
        return versions

    def _get_context(self):
        theme = self.request.GET.get('theme', False)
        docroot = self.request.GET.get('docroot', '')
        subproject = self.request.GET.get('subproject', False)
        source_suffix = self.request.GET.get('source_suffix', '.rst')

        new_theme = (theme == 'sphinx_rtd_theme')
        using_theme = (theme == 'default')

        project = self._get_project()
        main_project = project.main_language_project or project
        version = self._get_version()

        page_slug = self.request.GET.get('page', '')
        path = ''
        if page_slug and page_slug != 'index':
            if version.documentation_type == 'sphinx_htmldir':
                path = re.sub('/index$', '', page_slug) + '/'
            else:
                path = page_slug + '.html'

        context = {
            'project': project,
            'version': version,
            'path': path,
            'downloads': version.get_downloads(pretty=True),
            'current_version': version.verbose_name,
            'versions': self._get_active_versions_sorted(),
            'main_project': main_project,
            'translations': main_project.translations.all(),
            'current_language': project.language,
            'using_theme': using_theme,
            'new_theme': new_theme,
            'settings': settings,
            'subproject': subproject,
            'github_edit_url': version.get_github_url(
                docroot,
                page_slug,
                source_suffix,
                'edit',
            ),
            'github_view_url': version.get_github_url(
                docroot,
                page_slug,
                source_suffix,
                'view',
            ),
            'gitlab_edit_url': version.get_gitlab_url(
                docroot,
                page_slug,
                source_suffix,
                'edit',
            ),
            'gitlab_view_url': version.get_gitlab_url(
                docroot,
                page_slug,
                source_suffix,
                'view',
            ),
            'bitbucket_url': version.get_bitbucket_url(
                docroot,
                page_slug,
                source_suffix,
            ),
            'theme': theme,
        }
        return context

    def get(self, request, format=None):
        project = self._get_project()
        version = self._get_version()
        version_compare_data = get_version_compare_data(
            project,
            version,
        )

        context = self._get_context()
        html = template_loader.get_template('restapi/footer.html').render(
            context,
            request,
        )

        resp_data = {
            'html': html,
            'show_version_warning': project.show_version_warning,
            'version_active': version.active,
            'version_compare': version_compare_data,
            'version_supported': version.supported,
        }

        # Allow folks to hook onto the footer response for various information
        # collection, or to modify the resp_data.
        footer_response.send(
            sender=None,
            request=request,
            context=context,
            resp_data=resp_data,
        )

        return Response(resp_data)


class FooterHTML(SettingsOverrideObject):
    _default_class = BaseFooterHTML
