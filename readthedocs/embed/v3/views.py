"""Views for the EmbedAPI v3 app."""

import re
import urllib.parse
from urllib.parse import urlparse

import requests
import structlog
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from selectolax.parser import HTMLParser

from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.api.mixins import EmbedAPIMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.api.v3.permissions import HasEmbedAPIAccess
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.utils import clean_references
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)


class IsAuthorizedToGetContenFromVersion(IsAuthorizedToViewVersion):
    """
    Checks if the user from the request has permissions to get content from the version.

    If the URL is from an external site, we return ``True``,
    since we don't have a project to check for.
    """

    def has_permission(self, request, view):
        if view.external:
            return True
        return super().has_permission(request, view)


class EmbedAPIBase(EmbedAPIMixin, CDNCacheTagsMixin, APIView):
    # pylint: disable=line-too-long

    """
    Embed a section of content from any Read the Docs page.

    ### Arguments

    * url (with fragment) (required)
    * doctool
    * doctoolversion
    * maincontent

    ### Example

    GET https://readthedocs.org/api/v3/embed/?url=https://docs.readthedocs.io/en/latest/features.html%23full-text-search

    """  # noqa

    permission_classes = [HasEmbedAPIAccess, IsAuthorizedToGetContenFromVersion]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    @property
    def external(self):
        # NOTE: ``readthedocs.core.unresolver.unresolve`` returns ``None`` when
        # it can't find the project in our database
        return self.unresolved_url is None

    def _download_page_content(self, url):
        # Sanitize the URL before requesting it
        url = urlparse(url)._replace(fragment="", query="").geturl()

        # TODO: sanitize the cache key just in case, maybe by hashing it
        cache_key = f"embed-api-{url}"
        cached_response = cache.get(cache_key)
        if cached_response:
            log.debug("Cached response.", url=url)
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

    def _get_page_content_from_storage(self, project, version, filename):
        storage_path = project.get_storage_path(
            "html",
            version_slug=version.slug,
            include_file=False,
            version_type=version.type,
        )

        # Decode encoded URLs (e.g. convert %20 into a whitespace)
        filename = urllib.parse.unquote(filename)

        # If the filename starts with `/`, the join will fail,
        # so we strip it before joining it.
        relative_filename = filename.lstrip("/")
        file_path = build_media_storage.join(
            storage_path,
            relative_filename,
        )

        tryfiles = [file_path, build_media_storage.join(file_path, "index.html")]
        for tryfile in tryfiles:
            try:
                with build_media_storage.open(tryfile) as fd:
                    return fd.read()
            except Exception:  # noqa
                log.warning("Unable to read file.", file_path=file_path)

        return None

    def _get_content_by_fragment(
        self,
        url,
        fragment,
        doctool,
        doctoolversion,
        selector,
    ):
        if self.external:
            page_content = self._download_page_content(url)
        else:
            project = self.unresolved_url.project
            version = self.unresolved_url.version
            filename = self.unresolved_url.filename
            page_content = self._get_page_content_from_storage(project, version, filename)

        return self._parse_based_on_doctool(
            page_content,
            fragment,
            doctool,
            doctoolversion,
            selector,
        )

    def _find_main_node(self, html, selector):
        if selector:
            try:
                return html.css_first(selector)
            except ValueError:
                log.warning("Invalid CSS selector provided.", selector=selector)
                return None

        main_node = html.css_first("[role=main]")
        if main_node:
            log.debug("Main node found. selector=[role=main]")
            return main_node

        main_node = html.css_first("main")
        if main_node:
            log.debug("Main node found. selector=main")
            return main_node

        first_header = html.body.css_first("h1")
        if first_header:
            log.debug("Main node found. selector=h1")
            return first_header.parent

    def _parse_based_on_doctool(
        self,
        page_content,
        fragment,
        doctool,
        doctoolversion,
        selector,
    ):
        # pylint: disable=unused-argument disable=too-many-nested-blocks
        if not page_content:
            return

        node = None
        if fragment:
            # NOTE: we use the `[id=]` selector because using `#{id}` requires
            # escaping the selector since CSS does not support the same
            # characters as the `id=` HTML attribute
            # https://www.w3.org/TR/CSS21/syndata.html#value-def-identifier
            selector = f'[id="{fragment}"]'
            try:
                node = HTMLParser(page_content).css_first(selector)
            except ValueError:
                log.warning("Invalid CSS selector from fragment.", fragment=fragment)
                node = None
        else:
            html = HTMLParser(page_content)
            node = self._find_main_node(html, selector)

        if not node:
            return

        if doctool == "sphinx":
            # Handle manual reference special cases
            # See https://github.com/readthedocs/sphinx-hoverxref/issues/199
            if node.tag == "span" and not node.text():
                if any(
                    [
                        # docutils <0.18
                        all(
                            [
                                node.parent.tag == "div",
                                "section" in node.parent.attributes.get("class", []),
                            ]
                        ),
                        # docutils >=0.18
                        all(
                            [
                                node.parent.tag == "section",
                                node.parent.attributes.get("id", None),
                            ]
                        ),
                    ]
                ):
                    # Sphinx adds an empty ``<span id="my-reference"></span>``
                    # HTML tag when using manual references (``..
                    # _my-reference:``). Then, when users refer to it via
                    # ``:ref:`my-referece``` the API will return the empty
                    # span. If the parent node is a section, we have to return
                    # the parent node that will have the content expected.

                    # Structure:
                    # <section id="ref-section">
                    # <span id="ref-manual"></span>
                    # <h2>Ref Section<a class="headerlink" href="#ref-section">¶</a></h2>
                    # <p>This is a reference to
                    # <a class="reference internal" href="#ref-manual"><span>Ref Section</span></a>.
                    # </p>
                    # </section>
                    node = node.parent

            # Handle ``dt`` special cases
            if node.tag == "dt":
                if any(
                    [
                        "glossary" in node.parent.attributes.get("class"),
                        "citation" in node.parent.attributes.get("class"),
                    ]
                ):
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
                    if "glossary" in node.parent.attributes.get("class"):
                        # iterate through child and next nodes
                        traverse = node.traverse()
                        iteration = 0
                        while iteration < 5:
                            next_node = next(traverse, None)
                            # TODO: Do we need to support terms with missing descriptions?
                            # This will not produce correct results in this case.

                            # Stop at the next 'dd' node, which is the description
                            if iteration >= 5 or (next_node and next_node.tag == "dd"):
                                break
                            iteration += 1

                    elif "citation" in node.parent.attributes.get("class"):
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
        url = request.GET.get("url")
        doctool = request.GET.get("doctool")
        doctoolversion = request.GET.get("doctoolversion")
        selector = request.GET.get("maincontent")

        if not url:
            return Response(
                {"error": ('Invalid arguments. Please provide "url".')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if not domain or not parsed_url.scheme:
            return Response(
                {"error": (f"The URL requested is malformed. url={url}")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if self.external:
            for allowed_domain in settings.RTD_EMBED_API_EXTERNAL_DOMAINS:
                if re.match(allowed_domain, domain):
                    break
            else:
                log.info("Domain not allowed.", domain=domain, url=url)
                return Response(
                    {"error": (f"External domain not allowed. domain={domain}")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check rate-limit for this particular domain
            cache_key = f"embed-api-{domain}"
            cache.get_or_set(cache_key, 0, timeout=settings.RTD_EMBED_API_DOMAIN_RATE_LIMIT_TIMEOUT)
            cache.incr(cache_key)
            if cache.get(cache_key) > settings.RTD_EMBED_API_DOMAIN_RATE_LIMIT:
                log.warning("Too many requests for this domain.", domain=domain)
                return Response(
                    {"error": (f"Too many requests for this domain. domain={domain}")},
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
                doctool,
                doctoolversion,
                selector,
            )
        except requests.exceptions.TooManyRedirects:
            log.exception("Too many redirects.", url=url)
            return Response(
                {"error": (f"The URL requested generates too many redirects. url={url}")},
                # TODO: review these status codes to find out which on is better here
                # 400 Bad Request
                # 502 Bad Gateway
                # 503 Service Unavailable
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:  # noqa
            log.exception("There was an error reading the URL requested.", url=url)
            return Response(
                {"error": (f"There was an error reading the URL requested. url={url}")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not content_requested:
            log.warning(
                "Identifier not found.",
                url=url,
                fragment=fragment,
                maincontent=selector,
            )
            return Response(
                {
                    "error": (
                        "Can't find content for section: "
                        f"url={url} fragment={fragment} maincontent={selector}"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Sanitize the URL before requesting it
        sanitized_url = urlparse(url)._replace(fragment="", query="").geturl()
        # Make links from the content to be absolute
        content = clean_references(
            content_requested,
            sanitized_url,
            html_raw_response=True,
        )

        response = {
            "url": url,
            "fragment": fragment if fragment else None,
            "content": content,
            "external": self.external,
        }
        log.info(
            "EmbedAPI successful response.",
            project_slug=self.unresolved_url.project.slug if not self.external else None,
            domain=domain if self.external else None,
            doctool=doctool,
            doctoolversion=doctoolversion,
            url=url,
            referer=request.headers.get("Referer"),
            external=self.external,
            hoverxref_version=request.headers.get("X-Hoverxref-Version"),
        )
        return Response(response)


class EmbedAPI(SettingsOverrideObject):
    _default_class = EmbedAPIBase
