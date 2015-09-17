from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
import logging
import re

from readthedocs.projects.models import Project


log = logging.getLogger(__name__)


def redirect_filename(project, filename=None):
    """
    Return a url for a page. Always use http for now,
    to avoid content warnings.
    """
    protocol = "http"
    # Handle explicit http redirects
    if filename.startswith(protocol):
        return filename
    version = project.get_default_version()
    lang = project.language
    use_subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
    if use_subdomain:
        if project.single_version:
            return "%s://%s/%s" % (
                protocol,
                project.subdomain,
                filename,
            )
        else:
            return "%s://%s/%s/%s/%s" % (
                protocol,
                project.subdomain,
                lang,
                version,
                filename,
            )
    else:
        if project.single_version:
            return reverse('docs_detail', kwargs={
                'project_slug': project.slug,
                'filename': filename,
            })
        else:
            return reverse('docs_detail', kwargs={
                'project_slug': project.slug,
                'lang_slug': lang,
                'version_slug': version,
                'filename': filename,
            })


def get_redirect_url(project, path):
    for project_redirect in project.redirects.all():
        if project_redirect.redirect_type == 'prefix':
            if path.startswith(project_redirect.from_url):
                log.debug('Redirecting %s' % project_redirect)
                cut_path = re.sub('^%s' % project_redirect.from_url, '', path)
                to = redirect_filename(project=project, filename=cut_path)
                return to
        elif project_redirect.redirect_type == 'page':
            if path == project_redirect.from_url:
                log.debug('Redirecting %s' % project_redirect)
                to = redirect_filename(
                    project=project,
                    filename=project_redirect.to_url.lstrip('/'))
                return to
        elif project_redirect.redirect_type == 'exact':
            if path == project_redirect.from_url:
                log.debug('Redirecting %s' % project_redirect)
                return project_redirect.to_url
            # Handle full sub-level redirects
            if '$rest' in project_redirect.from_url:
                match = project_redirect.from_url.split('$rest')[0]
                if path.startswith(match):
                    cut_path = re.sub('^%s' % match, project_redirect.to_url, path)
                    return cut_path
        elif project_redirect.redirect_type == 'sphinx_html':
            if path.endswith('/'):
                log.debug('Redirecting %s' % project_redirect)
                to = re.sub('/$', '.html', path)
                return to
        elif project_redirect.redirect_type == 'sphinx_htmldir':
            if path.endswith('.html'):
                log.debug('Redirecting %s' % project_redirect)
                to = re.sub('.html$', '/', path)
                return to


def get_redirect_response(request, full_path=None):
    project = project_slug = None
    if hasattr(request, 'slug'):
        project_slug = request.slug
    elif full_path.startswith('/docs/'):
        split = full_path.split('/')
        if len(split) > 2:
            project_slug = split[2]
    else:
        return None

    if project_slug:
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return None

    if project:
        new_path = get_redirect_url(project, full_path)
        if not new_path is not None:
            return HttpResponseRedirect(new_path)
    return None
