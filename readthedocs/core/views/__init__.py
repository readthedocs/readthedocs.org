"""
Core views, including the main homepage,
documentation and header rendering, and server errors.
"""

import re
import os
import logging


from django.contrib import admin, messages
from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.utils import broadcast, send_email
from readthedocs.core.forms import SendEmailForm
from readthedocs.donate.mixins import DonateProgressMixin
from readthedocs.projects import constants
from readthedocs.projects.models import Project, ImportedFile
from readthedocs.projects.tasks import remove_dir
from readthedocs.redirects.utils import get_redirect_response

log = logging.getLogger(__name__)
pc_log = logging.getLogger(__name__ + '.post_commit')


class NoProjectException(Exception):
    pass


class HomepageView(DonateProgressMixin, TemplateView):

    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        '''Add latest builds and featured projects'''
        context = super(HomepageView, self).get_context_data(**kwargs)
        latest = []
        latest_builds = (
            Build.objects
            .filter(
                project__privacy_level=constants.PUBLIC,
                success=True,
            )
            .order_by('-date')
        )[:100]
        for build in latest_builds:
            if (build.project not in latest and len(latest) < 10):
                latest.append(build.project)
        context['project_list'] = latest
        context['featured_list'] = Project.objects.filter(featured=True)
        return context


class SupportView(TemplateView):
    template_name = 'support.html'

    def get_context_data(self, **kwargs):
        context = super(SupportView, self).get_context_data(**kwargs)
        support_email = getattr(settings, 'SUPPORT_EMAIL', None)
        if not support_email:
            support_email = 'support@{domain}'.format(
                domain=getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'))

        context['support_email'] = support_email
        return context


def random_page(request, project_slug=None):
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
    version = get_object_or_404(Version, project__slug=project_slug,
                                slug=version_slug)
    if request.user not in version.project.users.all():
        raise Http404("You must own this project to wipe it.")

    if request.method == 'POST':
        del_dirs = [
            os.path.join(version.project.doc_path, 'checkouts', version.slug),
            os.path.join(version.project.doc_path, 'envs', version.slug),
            os.path.join(version.project.doc_path, 'conda', version.slug),
        ]
        for del_dir in del_dirs:
            broadcast(type='build', task=remove_dir, args=[del_dir])
        return redirect('project_version_list', project_slug)
    else:
        return render_to_response('wipe_version.html',
                                  context_instance=RequestContext(request))


def divide_by_zero(request):
    return 1 / 0


def server_error(request, template_name='500.html'):
    """
    A simple 500 handler so we get media
    """
    r = render_to_response(template_name,
                           context_instance=RequestContext(request))
    r.status_code = 500
    return r


def server_error_404(request, template_name='404.html'):
    """
    A simple 404 handler so we get media
    """
    response = get_redirect_response(request, path=request.get_full_path())
    if response:
        return response
    r = render_to_response(template_name,
                           context_instance=RequestContext(request))
    r.status_code = 404
    return r


def server_helpful_404(
        request, project_slug=None, lang_slug=None, version_slug=None,
        filename=None, template_name='404.html'):
    response = get_redirect_response(request, path=filename)
    if response:
        return response
    pagename = re.sub(
        r'/index$', r'', re.sub(r'\.html$', r'', re.sub(r'/$', r'', filename)))
    suggestion = get_suggestion(
        project_slug, lang_slug, version_slug, pagename, request.user)
    r = render_to_response(template_name,
                           {'suggestion': suggestion},
                           context_instance=RequestContext(request))
    r.status_code = 404
    return r


def get_suggestion(project_slug, lang_slug, version_slug, pagename, user):
    """
    | # | project | version | language | What to show |
    | 1 |    0    |    0    |     0    | Error message |
    | 2 |    0    |    0    |     1    | Error message (Can't happen) |
    | 3 |    0    |    1    |     0    | Error message (Can't happen) |
    | 4 |    0    |    1    |     1    | Error message (Can't happen) |
    | 5 |    1    |    0    |     0    | A link to top-level page of default version |
    | 6 |    1    |    0    |     1    | Available versions on the translation project |
    | 7 |    1    |    1    |     0    | Available translations of requested version |
    | 8 |    1    |    1    |     1    | A link to top-level page of requested version |
    """

    suggestion = {}
    if project_slug:
        try:
            proj = Project.objects.get(slug=project_slug)
            if not lang_slug:
                lang_slug = proj.language
            try:
                ver = Version.objects.get(
                    project__slug=project_slug, slug=version_slug)
            except Version.DoesNotExist:
                ver = None

            if ver:  # if requested version is available on main project
                if lang_slug != proj.language:
                    try:
                        translations = proj.translations.filter(
                            language=lang_slug)
                        if translations:
                            ver = Version.objects.get(
                                project__slug=translations[0].slug, slug=version_slug)
                        else:
                            ver = None
                    except Version.DoesNotExist:
                        ver = None
                # if requested version is available on translation project too
                if ver:
                    # Case #8: Show a link to top-level page of the version
                    suggestion['type'] = 'top'
                    suggestion['message'] = "What are you looking for?"
                    suggestion['href'] = proj.get_docs_url(ver.slug, lang_slug)
                # requested version is available but not in requested language
                else:
                    # Case #7: Show available translations of the version
                    suggestion['type'] = 'list'
                    suggestion['message'] = (
                        "Requested page seems not to be translated in "
                        "requested language. But it's available in these "
                        "languages.")
                    suggestion['list'] = []
                    suggestion['list'].append({
                        'label': proj.language,
                        'project': proj,
                        'version_slug': version_slug,
                        'pagename': pagename
                    })
                    for t in proj.translations.all():
                        try:
                            Version.objects.get(
                                project__slug=t.slug, slug=version_slug)
                            suggestion['list'].append({
                                'label': t.language,
                                'project': t,
                                'version_slug': version_slug,
                                'pagename': pagename
                            })
                        except Version.DoesNotExist:
                            pass
            else:  # requested version does not exist on main project
                if lang_slug == proj.language:
                    trans = proj
                else:
                    translations = proj.translations.filter(language=lang_slug)
                    trans = translations[0] if translations else None
                if trans:  # requested language is available
                    # Case #6: Show available versions of the translation
                    suggestion['type'] = 'list'
                    suggestion['message'] = (
                        "Requested version seems not to have been built yet. "
                        "But these versions are available.")
                    suggestion['list'] = []
                    for v in Version.objects.public(user, trans, True):
                        suggestion['list'].append({
                            'label': v.slug,
                            'project': trans,
                            'version_slug': v.slug,
                            'pagename': pagename
                        })
                # requested project exists but requested version and language
                # are not available.
                else:
                    # Case #5: Show a link to top-level page of default version
                    # of main project
                    suggestion['type'] = 'top'
                    suggestion['message'] = 'What are you looking for??'
                    suggestion['href'] = proj.get_docs_url()
        except Project.DoesNotExist:
            # Case #1-4: Show error mssage
            suggestion['type'] = 'none'
            suggestion[
                'message'] = "We're sorry, we don't know what you're looking for"
    else:
        suggestion['type'] = 'none'
        suggestion[
            'message'] = "We're sorry, we don't know what you're looking for"

    return suggestion


class SendEmailView(FormView):

    """Form view for sending emails to users from admin pages
    Accepts the following additional parameters:
    queryset
        The queryset to use to determine the users to send emails to
    """

    form_class = SendEmailForm
    template_name = 'core/send_email_form.html'

    def get_form_kwargs(self):
        """Override form kwargs based on input fields
        The admin posts to this view initially, so detect the send button on
        form post variables. Drop additional fields if we see the send button.
        """
        kwargs = super(SendEmailView, self).get_form_kwargs()
        if 'send' not in self.request.POST:
            kwargs.pop('data', None)
            kwargs.pop('files', None)
        return kwargs

    def get_initial(self):
        """Add selected ids to initial form data"""
        initial = super(SendEmailView, self).get_initial()
        initial['_selected_action'] = self.request.POST.getlist(
            admin.ACTION_CHECKBOX_NAME)
        return initial

    def form_valid(self, form):
        """If form is valid, send emails to selected users"""
        count = 0
        for user in self.get_queryset().all():
            send_email(
                user.email,
                subject=form.cleaned_data['subject'],
                template='core/email/common.txt',
                template_html='core/email/common.html',
                context={'user': user, 'content': form.cleaned_data['body']},
                request=self.request,
            )
            count += 1
        if count == 0:
            self.message_user("No receipients to send to", level=messages.ERROR)
        else:
            self.message_user("Queued {0} messages".format(count))
        return HttpResponseRedirect(self.request.get_full_path())

    def get_queryset(self):
        return self.kwargs.get('queryset')

    def get_context_data(self, **kwargs):
        """Return queryset in context"""
        context = super(SendEmailView, self).get_context_data(**kwargs)
        context['users'] = self.get_queryset().all()
        return context

    def message_user(self, message, level=messages.INFO, extra_tags='',
                     fail_silently=False):
        """Implementation of :py:meth:`django.contrib.admin.options.ModelAdmin.message_user`
        Send message through messages framework
        """
        # TODO generalize this or check if implementation in ModelAdmin is
        # useable here
        messages.add_message(self.request, level, message, extra_tags=extra_tags,
                             fail_silently=fail_silently)
