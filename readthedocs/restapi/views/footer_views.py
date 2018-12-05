# -*- coding: utf-8 -*-
"""Endpoint to generate footer HTML."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import six
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import loader as template_loader
from rest_framework import decorators, permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_jsonp.renderers import JSONPRenderer

from readthedocs.builds.constants import LATEST, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.version_handling import (
    highest_version, parse_version_failsafe)
from readthedocs.restapi.signals import footer_response


def get_version_compare_data(project, base_version=None):
    """
    Retrieve metadata about the highest version available for this project.

    :param base_version: We assert whether or not the base_version is also the
                         highest version in the resulting "is_highest" value.
    """
    versions_qs = project.versions.public().filter(active=True)

    # Take preferences over tags only if the project has at least one tag
    if versions_qs.filter(type=TAG).exists():
        versions_qs = versions_qs.filter(type=TAG)

    highest_version_obj, highest_version_comparable = highest_version(
        versions_qs)
    ret_val = {
        'project': six.text_type(highest_version_obj),
        'version': six.text_type(highest_version_comparable),
        'is_highest': True,
    }
    if highest_version_obj:
        ret_val['url'] = highest_version_obj.get_absolute_url()
        ret_val['slug'] = highest_version_obj.slug
    if base_version and base_version.slug != LATEST:
        try:
            base_version_comparable = parse_version_failsafe(
                base_version.verbose_name)
            if base_version_comparable:
                # This is only place where is_highest can get set. All error
                # cases will be set to True, for non- standard versions.
                ret_val['is_highest'] = (
                    base_version_comparable >= highest_version_comparable)
            else:
                ret_val['is_highest'] = True
        except (Version.DoesNotExist, TypeError):
            ret_val['is_highest'] = True
    return ret_val


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer))
def footer_html(request):
    """Render and return footer markup."""
    # TODO refactor this function
    # pylint: disable=too-many-locals
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', None)
    page_slug = request.GET.get('page', None)
    theme = request.GET.get('theme', False)
    docroot = request.GET.get('docroot', '')
    subproject = request.GET.get('subproject', False)
    source_suffix = request.GET.get('source_suffix', '.rst')

    # Hack in a fix for missing version slug deploy that went out a while back
    if version_slug == '':
        version_slug = LATEST

    new_theme = (theme == 'sphinx_rtd_theme')
    using_theme = (theme == 'default')
    project = get_object_or_404(Project, slug=project_slug)
    version = get_object_or_404(
        Version.objects.public(
            request.user, project=project, only_active=False),
        slug__iexact=version_slug)
    main_project = project.main_language_project or project

    if page_slug and page_slug != 'index':
        if (main_project.documentation_type == 'sphinx_htmldir' or
                main_project.documentation_type == 'mkdocs'):
            path = page_slug + '/'
        elif main_project.documentation_type == 'sphinx_singlehtml':
            path = 'index.html#document-' + page_slug
        else:
            path = page_slug + '.html'
    else:
        path = ''

    version_compare_data = get_version_compare_data(project, version)

    context = {
        'project': project,
        'version': version,
        'path': path,
        'downloads': version.get_downloads(pretty=True),
        'current_version': version.verbose_name,
        'versions': project.ordered_active_versions(user=request.user),
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
