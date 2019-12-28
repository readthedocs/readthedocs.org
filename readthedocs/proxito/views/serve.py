"""Views for doc serving."""

import itertools
import logging
import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import resolve as url_resolve
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page

from readthedocs.builds.constants import LATEST, STABLE
from readthedocs.builds.models import Version
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects import constants
from readthedocs.projects.templatetags.projects_tags import sort_version_aware

from .mixins import ServeDocsMixin, ServeRedirectMixin

from .decorators import map_project_slug
from .redirects import redirect_project_slug
from .utils import _get_project_data_from_request


log = logging.getLogger(__name__)  # noqa


class ServeDocsBase(ServeRedirectMixin, ServeDocsMixin, View):

    def get(self,
            request,
            project_slug=None,
            subproject_slug=None,
            lang_slug=None,
            version_slug=None,
            filename='',
    ):  # noqa
        """Take the incoming parsed URL's and figure out what file to serve."""

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

        # Handle a / redirect when we aren't a single version
        if all([lang_slug is None, version_slug is None, filename == '',
                not final_project.single_version]):
            redirect_to = redirect_project_slug(
                request,
                project=final_project,
                subproject=None,
            )
            log.info(
                'Proxito redirect: from=%s, to=%s, project=%s', filename,
                redirect_to, final_project.slug
            )
            return redirect_to

        if (lang_slug is None or version_slug is None) and not final_project.single_version:
            log.info(
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
            type_='html', version_slug=version_slug, include_file=False
        )

        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

        # If ``filename`` is ``''`` it leaves a trailing slash
        path = os.path.join(storage_path, filename)

        url = storage.url(path)  # this will remove the trailing slash
        # URL without scheme and domain to perform an NGINX internal redirect
        url = urlparse(url)._replace(scheme='', netloc='').geturl()

        # Handle our backend storage not supporting directory indexes,
        # so we need to append index.html when appropriate.
        if path[-1] == '/':
            url += '/index.html'

        return self._serve_docs(
            request,
            final_project=final_project,
            path=url,
        )

    def allowed_user(self, *args, **kwargs):
        return True


class ServeDocs(SettingsOverrideObject):
    _default_class = ServeDocsBase


class ServeError404Base(ServeRedirectMixin, View):

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

        # Parse the URL using the normal urlconf, so we get proper subdomain/translation data
        _, __, kwargs = url_resolve(
            proxito_path, urlconf='readthedocs.proxito.urls'
        )
        final_project, lang_slug, version_slug, filename = _get_project_data_from_request(  # noqa
            request,
            project_slug=kwargs.get('project_slug'),
            subproject_slug=kwargs.get('subproject_slug'),
            lang_slug=kwargs.get('lang_slug'),
            version_slug=kwargs.get('version_slug'),
            filename=kwargs.get('filename', ''),
        )

        # Check and perform redirects on 404 handler
        redirect_path, http_status = self.get_redirect(
            final_project,
            lang_slug,
            version_slug,
            filename,
            request.path,
        )
        if redirect_path and http_status:
            return self.get_redirect_response(request, redirect_path, http_status)

        storage_root_path = final_project.get_storage_path(
            type_='html',
            version_slug=version_slug,
            include_file=False,
        )
        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

        # First, check for dirhtml with slash
        for tryfile in ('index.html', 'README.html'):
            storage_filename_path = os.path.join(
                storage_root_path, filename, tryfile
            )
            log.debug(
                'Trying index filename: project=%s version=%s, file=%s',
                final_project.slug,
                version_slug,
                storage_filename_path,
            )
            if storage.exists(storage_filename_path):
                log.info(
                    'Redirecting to index file: project=%s version=%s, url=%s',
                    final_project.slug,
                    version_slug,
                    storage_filename_path,
                )
                # Use urlparse so that we maintain GET args in our redirect
                parts = urlparse(proxito_path)
                if tryfile == 'README.html':
                    new_path = os.path.join(parts.path, tryfile)
                else:
                    new_path = parts.path + '/'
                new_parts = parts._replace(path=new_path)
                resp = HttpResponseRedirect(new_parts.geturl())
                return resp

        # If that doesn't work, attempt to serve the 404 of the current version (version_slug)
        # Secondly, try to serve the 404 page for the default version
        # (project.get_default_version())
        for version_slug_404 in [version_slug, final_project.get_default_version()]:
            for tryfile in ('404.html', '404/index.html'):
                storage_root_path = final_project.get_storage_path(
                    type_='html',
                    version_slug=version_slug_404,
                    include_file=False,
                )
                storage_filename_path = os.path.join(storage_root_path, tryfile)
                if storage.exists(storage_filename_path):
                    log.debug(
                        'Serving custom 404.html page: [project: %s] [version: %s]',
                        final_project.slug,
                        version_slug_404,
                    )
                    resp = HttpResponse(storage.open(storage_filename_path).read())
                    resp.status_code = 404
                    return resp

        # Finally, return the default 404 page generated by Read the Docs
        resp = render(request, template_name)
        resp.status_code = 404
        return resp


class ServeError404(SettingsOverrideObject):
    _default_class = ServeError404Base


class ServeRobotsTXTBase(ServeDocsMixin, View):

    @method_decorator(map_project_slug)
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
            # If project is private or,
            project.privacy_level == constants.PRIVATE,
            # default version is private or,
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
            type_='html', version_slug=version_slug, include_file=False
        )
        path = os.path.join(storage_path, 'robots.txt')

        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
        if storage.exists(path):
            url = storage.url(path)
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
        return HttpResponse(
            'User-agent: *\nAllow: /\nSitemap: {}\n'.format(sitemap_url),
            content_type='text/plain',
        )


class ServeRobotsTXT(SettingsOverrideObject):
    _default_class = ServeRobotsTXTBase


class ServeSitemapXMLBase(View):

    @method_decorator(map_project_slug)
    @method_decorator(cache_page(60 * 60 * 24 * 3))  # 3 days
    def get(self, request, project):
        """
        Generate and serve a ``sitemap.xml`` for a particular ``project``.

        The sitemap is generated from all the ``active`` and public versions of
        ``project``. These versions are sorted by using semantic versioning
        prepending ``latest`` and ``stable`` (if they are enabled) at the beginning.

        Following this order, the versions are assigned priorities and change
        frequency. Starting from 1 and decreasing by 0.1 for priorities and starting
        from daily, weekly to monthly for change frequency.

        If the project is private, the view raises ``Http404``. On the other hand,
        if the project is public but a version is private, this one is not included
        in the sitemap.

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

        if project.privacy_level == constants.PRIVATE:
            raise Http404

        sorted_versions = sort_version_aware(
            Version.internal.public(
                project=project,
                only_active=True,
            ),
        )

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
                            private=False,
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
