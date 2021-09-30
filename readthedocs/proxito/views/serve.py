"""Views for doc serving."""

import itertools
import logging
from urllib.parse import urlparse

from readthedocs.core.resolver import resolve_path
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import resolve as url_resolve
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page

from readthedocs.builds.constants import EXTERNAL, LATEST, STABLE
from readthedocs.builds.models import Version
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects import constants
from readthedocs.projects.constants import SPHINX_HTMLDIR
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.redirects.exceptions import InfiniteRedirectException
from readthedocs.storage import build_media_storage

from .decorators import map_project_slug
from .mixins import ServeDocsMixin, ServeRedirectMixin
from .utils import _get_project_data_from_request

log = logging.getLogger(__name__)  # noqa


class ServePageRedirect(ServeRedirectMixin, ServeDocsMixin, View):
    def get(self,
            request,
            project_slug=None,
            subproject_slug=None,
            version_slug=None,
            filename='',
    ):  # noqa

        version_slug = self.get_version_from_host(request, version_slug)
        final_project, lang_slug, version_slug, filename = _get_project_data_from_request(  # noqa
            request,
            project_slug=project_slug,
            subproject_slug=subproject_slug,
            lang_slug=None,
            version_slug=version_slug,
            filename=filename,
        )
        return self.system_redirect(request, final_project, lang_slug, version_slug, filename)


class ServeDocsBase(ServeRedirectMixin, ServeDocsMixin, View):

    def get(self,
            request,
            project_slug=None,
            subproject_slug=None,
            subproject_slash=None,
            lang_slug=None,
            version_slug=None,
            filename='',
    ):  # noqa
        """
        Take the incoming parsed URL's and figure out what file to serve.

        ``subproject_slash`` is used to determine if the subproject URL has a slash,
        so that we can decide if we need to serve docs or add a /.
        """

        version_slug = self.get_version_from_host(request, version_slug)
        final_project, lang_slug, version_slug, filename = _get_project_data_from_request(  # noqa
            request,
            project_slug=project_slug,
            subproject_slug=subproject_slug,
            lang_slug=lang_slug,
            version_slug=version_slug,
            filename=filename,
        )

        log.debug(
            'Serving docs: project=%s, subproject=%s, lang_slug=%s, version_slug=%s, filename=%s',
            final_project.slug, subproject_slug, lang_slug, version_slug, filename
        )

        # Handle requests that need canonicalizing (eg. HTTP -> HTTPS, redirect to canonical domain)
        if hasattr(request, 'canonicalize'):
            try:
                return self.canonical_redirect(request, final_project, version_slug, filename)
            except InfiniteRedirectException:
                # Don't redirect in this case, since it would break things
                pass

        # Handle a / redirect when we aren't a single version
        if all([
                lang_slug is None,
                # External versions/builds will always have a version,
                # because it is taken from the host name
                version_slug is None or hasattr(request, 'external_domain'),
                filename == '',
                not final_project.single_version,
        ]):
            return self.system_redirect(request, final_project, lang_slug, version_slug, filename)

        # Handle `/projects/subproject` URL redirection:
        # when there _is_ a subproject_slug but not a subproject_slash
        if all([
                final_project.single_version,
                filename == '',
                subproject_slug,
                not subproject_slash,
        ]):
            return self.system_redirect(request, final_project, lang_slug, version_slug, filename)

        if all([
                (lang_slug is None or version_slug is None),
                not final_project.single_version,
                self.version_type != EXTERNAL,
        ]):
            log.warning(
                'Invalid URL for project with versions. url=%s, project=%s',
                filename, final_project.slug
            )
            raise Http404('Invalid URL for project with versions')

        # TODO: un-comment when ready to perform redirect here
        # redirect_path, http_status = self.get_redirect(
        #     final_project,
        #     lang_slug,
        #     version_slug,
        #     filename,
        #     request.path,
        # )
        # if redirect_path and http_status:
        #     return self.get_redirect_response(request, redirect_path, http_status)

        # Check user permissions and return an unauthed response if needed
        if not self.allowed_user(request, final_project, version_slug):
            return self.get_unauthed_response(request, final_project)

        storage_path = final_project.get_storage_path(
            type_='html',
            version_slug=version_slug,
            include_file=False,
            version_type=self.version_type,
        )

        # If ``filename`` is empty, serve from ``/``
        path = build_media_storage.join(storage_path, filename.lstrip('/'))
        # Handle our backend storage not supporting directory indexes,
        # so we need to append index.html when appropriate.
        if path[-1] == '/':
            # We need to add the index.html before ``storage.url`` since the
            # Signature and Expire time is calculated per file.
            path += 'index.html'

        # NOTE: calling ``.url`` will remove the trailing slash
        storage_url = build_media_storage.url(path, http_method=request.method)

        # URL without scheme and domain to perform an NGINX internal redirect
        parsed_url = urlparse(storage_url)._replace(scheme='', netloc='')
        final_url = parsed_url.geturl()

        return self._serve_docs(
            request,
            final_project=final_project,
            version_slug=version_slug,
            path=final_url,
        )


class ServeDocs(SettingsOverrideObject):
    _default_class = ServeDocsBase


class ServeError404Base(ServeRedirectMixin, ServeDocsMixin, View):

    def get(self, request, proxito_path, template_name='404.html'):
        """
        Handler for 404 pages on subdomains.

        This does a couple things:

        * Handles directory indexing for URLs that don't end in a slash
        * Handles directory indexing for README.html (for now)
        * Handles custom 404 serving

        For 404's, first search for a 404 page in the current version, then continues
        with the default version and finally, if none of them are found, the Read
        the Docs default page (Maze Found) is rendered by Django and served.
        """
        # pylint: disable=too-many-locals
        log.info('Executing 404 handler. proxito_path=%s', proxito_path)

        # Parse the URL using the normal urlconf, so we get proper subdomain/translation data
        _, __, kwargs = url_resolve(
            proxito_path,
            urlconf='readthedocs.proxito.urls',
        )

        version_slug = kwargs.get('version_slug')
        version_slug = self.get_version_from_host(request, version_slug)
        final_project, lang_slug, version_slug, filename = _get_project_data_from_request(  # noqa
            request,
            project_slug=kwargs.get('project_slug'),
            subproject_slug=kwargs.get('subproject_slug'),
            lang_slug=kwargs.get('lang_slug'),
            version_slug=version_slug,
            filename=kwargs.get('filename', ''),
        )

        storage_root_path = final_project.get_storage_path(
            type_='html',
            version_slug=version_slug,
            include_file=False,
            version_type=self.version_type,
        )

        # First, check for dirhtml with slash
        for tryfile in ('index.html', 'README.html'):
            storage_filename_path = build_media_storage.join(
                storage_root_path,
                f'{filename}/{tryfile}'.lstrip('/'),
            )
            log.debug(
                'Trying index filename: project=%s version=%s, file=%s',
                final_project.slug,
                version_slug,
                storage_filename_path,
            )
            if build_media_storage.exists(storage_filename_path):
                log.info(
                    'Redirecting to index file: project=%s version=%s, storage_path=%s',
                    final_project.slug,
                    version_slug,
                    storage_filename_path,
                )
                # Use urlparse so that we maintain GET args in our redirect
                parts = urlparse(proxito_path)
                if tryfile == 'README.html':
                    new_path = parts.path.rstrip('/') + f'/{tryfile}'
                else:
                    new_path = parts.path.rstrip('/') + '/'

                # `proxito_path` doesn't include query params.`
                query = urlparse(request.get_full_path()).query
                new_parts = parts._replace(
                    path=new_path,
                    query=query,
                )
                redirect_url = new_parts.geturl()

                # TODO: decide if we need to check for infinite redirect here
                # (from URL == to URL)
                return HttpResponseRedirect(redirect_url)

        # ``redirect_filename`` is the path without ``/<lang>/<version>`` and
        # without query, starting with a ``/``. This matches our old logic:
        # https://github.com/readthedocs/readthedocs.org/blob/4b09c7a0ab45cd894c3373f7f07bad7161e4b223/readthedocs/redirects/utils.py#L60
        # We parse ``filename`` to remove the query from it
        schema, netloc, path, params, query, fragments = urlparse(filename)
        redirect_filename = path

        # we can't check for lang and version here to decide if we need to add
        # the ``/`` or not because ``/install.html`` is a valid path to use as
        # redirect and does not include lang and version on it. It should be
        # fine always adding the ``/`` to the beginning.
        redirect_filename = '/' + redirect_filename.lstrip('/')

        # Check and perform redirects on 404 handler
        # NOTE: this redirect check must be done after trying files like
        # ``index.html`` and ``README.html`` to emulate the behavior we had when
        # serving directly from NGINX without passing through Python.
        redirect_path, http_status = self.get_redirect(
            project=final_project,
            lang_slug=lang_slug,
            version_slug=version_slug,
            filename=redirect_filename,
            full_path=proxito_path,
        )
        if redirect_path and http_status:
            try:
                return self.get_redirect_response(request, redirect_path, proxito_path, http_status)
            except InfiniteRedirectException:
                # Continue with our normal 404 handling in this case
                pass

        # If that doesn't work, attempt to serve the 404 of the current version (version_slug)
        # Secondly, try to serve the 404 page for the default version
        # (project.get_default_version())
        doc_type = (
            Version.objects.filter(project=final_project, slug=version_slug)
            .values_list('documentation_type', flat=True)
            .first()
        )
        versions = [(version_slug, doc_type)]
        default_version_slug = final_project.get_default_version()
        if default_version_slug != version_slug:
            default_version_doc_type = (
                Version.objects.filter(project=final_project, slug=default_version_slug)
                .values_list('documentation_type', flat=True)
                .first()
            )
            versions.append((default_version_slug, default_version_doc_type))

        for version_slug_404, doc_type_404 in versions:
            if not self.allowed_user(request, final_project, version_slug_404):
                continue

            storage_root_path = final_project.get_storage_path(
                type_='html',
                version_slug=version_slug_404,
                include_file=False,
                version_type=self.version_type,
            )
            tryfiles = ['404.html']
            # SPHINX_HTMLDIR is the only builder
            # that could output a 404/index.html file.
            if doc_type_404 == SPHINX_HTMLDIR:
                tryfiles.append('404/index.html')
            for tryfile in tryfiles:
                storage_filename_path = build_media_storage.join(storage_root_path, tryfile)
                if build_media_storage.exists(storage_filename_path):
                    log.info(
                        'Serving custom 404.html page: [project: %s] [version: %s]',
                        final_project.slug,
                        version_slug_404,
                    )
                    resp = HttpResponse(build_media_storage.open(storage_filename_path).read())
                    resp.status_code = 404
                    return resp

        raise Http404('No custom 404 page found.')


class ServeError404(SettingsOverrideObject):
    _default_class = ServeError404Base


class ServeRobotsTXTBase(ServeDocsMixin, View):

    @method_decorator(map_project_slug)
    @method_decorator(cache_page(60 * 60))  # 1 hour
    def get(self, request, project):
        """
        Serve custom user's defined ``/robots.txt``.

        If the user added a ``robots.txt`` in the "default version" of the
        project, we serve it directly.
        """

        # Use the ``robots.txt`` file from the default version configured
        version_slug = project.get_default_version()
        version = project.versions.get(slug=version_slug)

        no_serve_robots_txt = any([
            # If the default version is private or,
            version.privacy_level == constants.PRIVATE,
            # default version is not active or,
            not version.active,
            # default version is not built
            not version.built,
        ])

        if no_serve_robots_txt:
            # ... we do return a 404
            raise Http404()

        storage_path = project.get_storage_path(
            type_='html',
            version_slug=version_slug,
            include_file=False,
            version_type=self.version_type,
        )
        path = build_media_storage.join(storage_path, 'robots.txt')

        if build_media_storage.exists(path):
            url = build_media_storage.url(path)
            url = urlparse(url)._replace(scheme='', netloc='').geturl()
            return self._serve_docs(
                request,
                final_project=project,
                path=url,
            )

        sitemap_url = '{scheme}://{domain}/sitemap.xml'.format(
            scheme='https',
            domain=project.subdomain(),
        )
        context = {
            'sitemap_url': sitemap_url,
            'hidden_paths': self._get_hidden_paths(project),
        }
        return render(
            request,
            'robots.txt',
            context,
            content_type='text/plain',
        )

    def _get_hidden_paths(self, project):
        """Get the absolute paths of the public hidden versions of `project`."""
        hidden_versions = (
            Version.internal.public(project=project)
            .filter(hidden=True)
        )
        hidden_paths = [
            resolve_path(project, version_slug=version.slug)
            for version in hidden_versions
        ]
        return hidden_paths


class ServeRobotsTXT(SettingsOverrideObject):
    _default_class = ServeRobotsTXTBase


class ServeSitemapXMLBase(View):

    @method_decorator(map_project_slug)
    @method_decorator(cache_page(60 * 60 * 12))  # 12 hours
    def get(self, request, project):
        """
        Generate and serve a ``sitemap.xml`` for a particular ``project``.

        The sitemap is generated from all the ``active`` and public versions of
        ``project``. These versions are sorted by using semantic versioning
        prepending ``latest`` and ``stable`` (if they are enabled) at the beginning.

        Following this order, the versions are assigned priorities and change
        frequency. Starting from 1 and decreasing by 0.1 for priorities and starting
        from daily, weekly to monthly for change frequency.

        If the project doesn't have any public version, the view raises ``Http404``.

        :param request: Django request object
        :param project: Project instance to generate the sitemap

        :returns: response with the ``sitemap.xml`` template rendered

        :rtype: django.http.HttpResponse
        """
        # pylint: disable=too-many-locals

        def priorities_generator():
            """
            Generator returning ``priority`` needed by sitemap.xml.

            It generates values from 1 to 0.1 by decreasing in 0.1 on each
            iteration. After 0.1 is reached, it will keep returning 0.1.
            """
            priorities = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            yield from itertools.chain(priorities, itertools.repeat(0.1))

        def hreflang_formatter(lang):
            """
            sitemap hreflang should follow correct format.

            Use hyphen instead of underscore in language and country value.
            ref: https://en.wikipedia.org/wiki/Hreflang#Common_Mistakes
            """
            if '_' in lang:
                return lang.replace('_', '-')
            return lang

        def changefreqs_generator():
            """
            Generator returning ``changefreq`` needed by sitemap.xml.

            It returns ``weekly`` on first iteration, then ``daily`` and then it
            will return always ``monthly``.

            We are using ``monthly`` as last value because ``never`` is too
            aggressive. If the tag is removed and a branch is created with the same
            name, we will want bots to revisit this.
            """
            changefreqs = ['weekly', 'daily']
            yield from itertools.chain(changefreqs, itertools.repeat('monthly'))

        public_versions = Version.internal.public(
            project=project,
            only_active=True,
        )
        if not public_versions.exists():
            raise Http404

        sorted_versions = sort_version_aware(public_versions)

        # This is a hack to swap the latest version with
        # stable version to get the stable version first in the sitemap.
        # We want stable with priority=1 and changefreq='weekly' and
        # latest with priority=0.9 and changefreq='daily'
        # More details on this: https://github.com/rtfd/readthedocs.org/issues/5447
        if (len(sorted_versions) >= 2 and sorted_versions[0].slug == LATEST and
                sorted_versions[1].slug == STABLE):
            sorted_versions[0], sorted_versions[1] = sorted_versions[1], sorted_versions[0]

        versions = []
        for version, priority, changefreq in zip(
                sorted_versions,
                priorities_generator(),
                changefreqs_generator(),
        ):
            element = {
                'loc': version.get_subdomain_url(),
                'priority': priority,
                'changefreq': changefreq,
                'languages': [],
            }

            # Version can be enabled, but not ``built`` yet. We want to show the
            # link without a ``lastmod`` attribute
            last_build = version.builds.order_by('-date').first()
            if last_build:
                element['lastmod'] = last_build.date.isoformat()

            if project.translations.exists():
                for translation in project.translations.all():
                    translation_versions = (
                        Version.internal.public(project=translation
                                                ).values_list('slug', flat=True)
                    )
                    if version.slug in translation_versions:
                        href = project.get_docs_url(
                            version_slug=version.slug,
                            lang_slug=translation.language,
                        )
                        element['languages'].append({
                            'hreflang': hreflang_formatter(translation.language),
                            'href': href,
                        })

                # Add itself also as protocol requires
                element['languages'].append({
                    'hreflang': project.language,
                    'href': element['loc'],
                })

            versions.append(element)

        context = {
            'versions': versions,
        }
        return render(
            request,
            'sitemap.xml',
            context,
            content_type='application/xml',
        )


class ServeSitemapXML(SettingsOverrideObject):
    _default_class = ServeSitemapXMLBase
