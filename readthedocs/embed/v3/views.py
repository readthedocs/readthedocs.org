"""Views for the EmbedAPI v3 app."""

import re
from urllib.parse import urlparse
import requests

import structlog

from selectolax.parser import HTMLParser

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.mixins import CachedResponseMixin
from readthedocs.core.unresolver import unresolve
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.utils import clean_links
from readthedocs.projects.constants import PUBLIC
from readthedocs.storage import build_media_storage

log = structlog.get_logger(__name__)


class EmbedAPIBase(CachedResponseMixin, APIView):

    # pylint: disable=line-too-long
    # pylint: disable=no-self-use

    """
    Embed a section of content from any Read the Docs page.

    ### Arguments

    * url (with fragment) (required)
    * doctool
    * doctoolversion

    ### Example

    GET https://readthedocs.org/api/v3/embed/?url=https://docs.readthedocs.io/en/latest/features.html%23full-text-search

    """  # noqa

    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    @cached_property
    def unresolved_url(self):
        url = self.request.GET.get('url')
        if not url:
            return None
        return unresolve(url)

    def _download_page_content(self, url):
        # Sanitize the URL before requesting it
        url = urlparse(url)._replace(fragment='', query='').geturl()

        # TODO: sanitize the cache key just in case, maybe by hashing it
        cache_key = f'embed-api-{url}'
        cached_response = cache.get(cache_key)
        if cached_response:
            log.debug('Cached response.', url=url)
            return cached_response

        response = requests.get(url, timeout=settings.RTD_EMBED_API_DEFAULT_REQUEST_TIMEOUT)
        if response.ok:
            # NOTE: we use ``response.content`` to get its binary
            # representation. Then ``selectolax`` is in charge to auto-detect
            # its encoding. We trust more in selectolax for this than in requests.
            cache.set(
                cache_key,
                response.content,
                timeout=settings.RTD_EMBED_API_PAGE_CACHE_TIMEOUT,
            )
            return response.content

    def _get_page_content_from_storage(self, project, version_slug, filename):
        version = get_object_or_404(
            project.versions,
            slug=version_slug,
            # Only allow PUBLIC versions when getting the content from our
            # storage for privacy/security reasons
            privacy_level=PUBLIC,
        )
        storage_path = project.get_storage_path(
            'html',
            version_slug=version.slug,
            include_file=False,
            version_type=version.type,
        )
        file_path = build_media_storage.join(
            storage_path,
            filename,
        )
        try:
            with build_media_storage.open(file_path) as fd:  # pylint: disable=invalid-name
                return fd.read()
        except Exception:  # noqa
            log.warning('Unable to read file.', file_path=file_path)

        return None

    def _get_content_by_fragment(self, url, fragment, external, doctool, doctoolversion):
        if external:
            page_content = self._download_page_content(url)
        else:
            project = self.unresolved_url.project
            version_slug = self.unresolved_url.version_slug
            filename = self.unresolved_url.filename
            page_content = self._get_page_content_from_storage(project, version_slug, filename)

        return self._parse_based_on_doctool(page_content, fragment, doctool, doctoolversion)

    def _find_main_node(self, html):
        main_node = html.css_first('[role=main]')
        if main_node:
            log.info('Main node found. selector=[role=main]')
            return main_node

        main_node = html.css_first('main')
        if main_node:
            log.info('Main node found. selector=main')
            return main_node

        first_header = html.body.css_first('h1')
        if first_header:
            log.info('Main node found. selector=h1')
            return first_header.parent

    def _parse_based_on_doctool(self, page_content, fragment, doctool, doctoolversion):
        # pylint: disable=unused-argument
        if not page_content:
            return

        node = None
        if fragment:
            # NOTE: we use the `[id=]` selector because using `#{id}` requires
            # escaping the selector since CSS does not support the same
            # characters as the `id=` HTML attribute
            # https://www.w3.org/TR/CSS21/syndata.html#value-def-identifier
            selector = f'[id="{fragment}"]'
            node = HTMLParser(page_content).css_first(selector)
        else:
            html = HTMLParser(page_content)
            node = self._find_main_node(html)

        if not node:
            return

        if doctool == 'sphinx':
            # Handle ``dt`` special cases
            if node.tag == 'dt':
                if any([
                        'glossary' in node.parent.attributes.get('class'),
                        'citation' in node.parent.attributes.get('class'),
                ]):
                    # Sphinx HTML structure for term glossary puts the ``id`` in the
                    # ``dt`` element with the title of the term. In this case, we
                    # return the parent node which contains the definition list
                    # and remove all ``dt/dd`` that are not the requested one

                    # Structure:
                    # <dl class="glossary docutils">
                    # <dt id="term-definition">definition</dt>
                    # <dd>Text definition for the term</dd>
                    # ...
                    # </dl>

                    parent_node = node.parent
                    if 'glossary' in node.parent.attributes.get('class'):
                        next_node = node.next

                    elif 'citation' in node.parent.attributes.get('class'):
                        next_node = node.next.next

                    # Iterate over all the siblings (``.iter()``) of the parent
                    # node and remove ``dt`` and ``dd`` that are not the ones
                    # we are looking for. Then return the parent node as
                    # result.
                    #
                    # Note that ``.iter()`` returns a generator and we modify
                    # the HTML in-place, so we have to convert it to a list
                    # before removing elements. Otherwise we break the
                    # iteration before completing it
                    for n in list(parent_node.iter()):  # pylint: disable=invalid-name
                        if n not in (node, next_node):
                            n.remove()
                    node = parent_node

                else:
                    # Sphinx HTML structure for definition list puts the ``id``
                    # the ``dt`` element, instead of the ``dl``. This makes
                    # the backend to return just the title of the definition. If we
                    # detect this case, we return the parent with the whole ``dl`` tag

                    # Structure:
                    # <dl class="confval">
                    # <dt id="confval-config">
                    # <code class="descname">config</code>
                    # <a class="headerlink" href="#confval-config">¶</a></dt>
                    # <dd><p>Text with a description</p></dd>
                    # </dl>
                    node = node.parent

        return node.html

    def get(self, request):  # noqa
        url = request.GET.get('url')
        doctool = request.GET.get('doctool')
        doctoolversion = request.GET.get('doctoolversion')

        if not url:
            return Response(
                {
                    'error': (
                        'Invalid arguments. '
                        'Please provide "url".'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if not domain or not parsed_url.scheme:
            return Response(
                {
                    'error': (
                        'The URL requested is malformed. '
                        f'url={url}'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # NOTE: ``readthedocs.core.unresolver.unresolve`` returns ``None`` when
        # it can't find the project in our database
        external = self.unresolved_url is None
        if external:
            for allowed_domain in settings.RTD_EMBED_API_EXTERNAL_DOMAINS:
                if re.match(allowed_domain, domain):
                    break
            else:
                log.info('Domain not allowed.', domain=domain, url=url)
                return Response(
                    {
                        'error': (
                            'External domain not allowed. '
                            f'domain={domain}'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check rate-limit for this particular domain
            cache_key = f'embed-api-{domain}'
            cache.get_or_set(cache_key, 0, timeout=settings.RTD_EMBED_API_DOMAIN_RATE_LIMIT_TIMEOUT)
            cache.incr(cache_key)
            if cache.get(cache_key) > settings.RTD_EMBED_API_DOMAIN_RATE_LIMIT:
                log.warning('Too many requests for this domain.', domain=domain)
                return Response(
                    {
                        'error': (
                            'Too many requests for this domain. '
                            f'domain={domain}'
                        )
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        # NOTE: we could validate the fragment if we want. It must contain at
        # least one character, cannot start with a number, and must not contain
        # whitespaces (spaces, tabs, etc.).
        fragment = parsed_url.fragment

        try:
            content_requested = self._get_content_by_fragment(
                url,
                fragment,
                external,
                doctool,
                doctoolversion,
            )
        except requests.exceptions.TooManyRedirects:
            log.exception('Too many redirects.', url=url)
            return Response(
                {
                    'error': (
                        'The URL requested generates too many redirects. '
                        f'url={url}'
                    )
                },
                # TODO: review these status codes to find out which on is better here
                # 400 Bad Request
                # 502 Bad Gateway
                # 503 Service Unavailable
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:  # noqa
            log.exception('There was an error reading the URL requested.', url=url)
            return Response(
                {
                    'error': (
                        'There was an error reading the URL requested. '
                        f'url={url}'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not content_requested:
            log.warning('Identifier not found.', url=url, fragment=fragment)
            return Response(
                {
                    'error': (
                        "Can't find content for section: "
                        f"url={url} fragment={fragment}"
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Sanitize the URL before requesting it
        sanitized_url = urlparse(url)._replace(fragment='', query='').geturl()
        # Make links from the content to be absolute
        content = clean_links(
            content_requested,
            sanitized_url,
            html_raw_response=True,
        )

        response = {
            'url': url,
            'fragment': fragment if fragment else None,
            'content': content,
            'external': external,
        }
        log.info(
            'EmbedAPI successful response.',
            project_slug=self.unresolved_url.project.slug if not external else None,
            domain=domain if external else None,
            doctool=doctool,
            doctoolversion=doctoolversion,
            url=url,
            referer=request.META.get('HTTP_REFERER'),
            external=external,
            hoverxref_version=request.META.get('HTTP_X_HOVERXREF_VERSION'),
        )
        return Response(response)


class EmbedAPI(SettingsOverrideObject):
    _default_class = EmbedAPIBase
