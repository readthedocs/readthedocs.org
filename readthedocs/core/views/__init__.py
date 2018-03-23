# -*- coding: utf-8 -*-
"""
Core views, including the main homepage,

documentation and header rendering, and server errors.
"""

from __future__ import absolute_import
from __future__ import division
from past.utils import old_div
import os
import logging

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.utils import broadcast
from readthedocs.projects import constants
from readthedocs.projects.models import Project, ImportedFile
from readthedocs.projects.tasks import remove_dir
from readthedocs.redirects.utils import get_redirect_response

log = logging.getLogger(__name__)


class NoProjectException(Exception):
    pass


class HomepageView(TemplateView):

    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        """Add latest builds and featured projects."""
        context = super(HomepageView, self).get_context_data(**kwargs)
        context['featured_list'] = Project.objects.filter(featured=True)
        context['projects_count'] = Project.objects.count()
        return context


class SupportView(TemplateView):
    template_name = 'support.html'

    def get_context_data(self, **kwargs):
        context = super(SupportView, self).get_context_data(**kwargs)
        support_email = getattr(settings, 'SUPPORT_EMAIL', None)
        if not support_email:
            support_email = 'support@{domain}'.format(
                domain=getattr(
                    settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'))

        context['support_email'] = support_email
        return context


def random_page(request, project_slug=None):  # pylint: disable=unused-argument
    imported_file = ImportedFile.objects.order_by('?')
    if project_slug:
        imported_file = imported_file.filter(project__slug=project_slug)
    imported_file = imported_file.first()
    if imported_file is None:
        raise Http404
    url = imported_file.get_absolute_url()
    return HttpResponseRedirect(url)


@csrf_exempt
def wipe_version(request, project_slug, version_slug):
    version = get_object_or_404(
        Version,
        project__slug=project_slug,
        slug=version_slug,
    )
    # We need to check by ``for_admin_user`` here to allow members of the
    # ``Admin`` team (which doesn't own the project) under the corporate site.
    if version.project not in Project.objects.for_admin_user(user=request.user):
        raise Http404('You must own this project to wipe it.')

    if request.method == 'POST':
        del_dirs = [
            os.path.join(version.project.doc_path, 'checkouts', version.slug),
            os.path.join(version.project.doc_path, 'envs', version.slug),
            os.path.join(version.project.doc_path, 'conda', version.slug),
        ]
        for del_dir in del_dirs:
            broadcast(type='build', task=remove_dir, args=[del_dir])
        return redirect('project_version_list', project_slug)
    return render(
        request, 'wipe_version.html',
        {'version': version, 'project': version.project})


def divide_by_zero(request):  # pylint: disable=unused-argument
    return old_div(1, 0)


def server_error_500(request, template_name='500.html'):
    """A simple 500 handler so we get media."""
    r = render(request, template_name)
    r.status_code = 500
    return r


def server_error_404(request, exception, template_name='404.html'):  # pylint: disable=unused-argument  # noqa
    """A simple 404 handler so we get media."""
    response = get_redirect_response(request, path=request.get_full_path())
    if response:
        return response
    r = render(request, template_name)
    r.status_code = 404
    return r
