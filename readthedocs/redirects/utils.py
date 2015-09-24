from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
import logging
import re

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


log = logging.getLogger(__name__)


def redirect_filename(project, filename, version=None):
    """
    Return a path for a page. No protocol/domain is returned.
    """

    protocol = "http"
    # Handle explicit http redirects
    if filename.startswith(protocol):
        return filename

    if version is None:
        version_slug = project.get_default_version()
    else:
        version_slug = version.slug

    language = project.language

    use_subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
    if use_subdomain:
        if project.single_version:
            return "/%s" % (filename,)
        else:
            return "/%s/%s/%s" % (language, version_slug, filename,)
    else:
        if project.single_version:
            return reverse('docs_detail', kwargs={
                'project_slug': project.slug,
                'filename': filename,
            })
        else:
            return reverse('docs_detail', kwargs={
                'project_slug': project.slug,
                'lang_slug': language,
                'version_slug': version_slug,
                'filename': filename,
            })


def get_redirect_url(project, path, version=None):
    """
    Redirect the given path for the given project. Will always return absolute
    paths, without domain.
    """
    for project_redirect in project.redirects.all():
        if project_redirect.redirect_type == 'prefix':
            if path.startswith(project_redirect.from_url):
                log.debug('Redirecting %s' % project_redirect)
                cut_path = re.sub('^%s' % project_redirect.from_url, '', path)
                to = redirect_filename(
                    project=project,
                    filename=cut_path,
                    version=version)
                return to
        elif project_redirect.redirect_type == 'page':
            if path == project_redirect.from_url:
                log.debug('Redirecting %s' % project_redirect)
                to = redirect_filename(
                    project=project,
                    filename=project_redirect.to_url.lstrip('/'),
                    version=version)
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


def get_redirect_response(request, path=None):
    project = project_slug = None
    if hasattr(request, 'slug'):
        project_slug = request.slug
    elif path.startswith('/docs/'):
        # In this case we use the docs without subdomains. So let's strip the
        # docs prefix.
        split = path.split('/')
        if len(split) > 2:
            project_slug = split[2]
            path = '/'.join(split[3:])
    else:
        return None

    if project_slug:
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return None

    if project:
        version = None
        if not project.single_version:
            match = re.match(
                r'^/(?P<language>[^/]+)/(?P<version_slug>[^/]+)/.*',
                path)
            if match:
                version_slug = match.groupdict()['version_slug']
                try:
                    version = project.versions.get(slug=version_slug)
                except Version.DoesNotExist:
                    pass

        new_path = get_redirect_url(project=project,
                                    path=path,
                                    version=version)
        if new_path is not None:
            # Re-use the domain and protocol used in the current request.
            # Redirects shouldn't change the domain, version or language.
            new_path = request.build_absolute_uri(new_path)
            return HttpResponseRedirect(new_path)
    return None
