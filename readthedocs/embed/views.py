"""Views for the embed app."""

import functools
import json
import logging
import re
from urllib.parse import urlparse

from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils.functional import cached_property
from docutils.nodes import make_id
from rest_framework import status
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from selectolax.parser import HTMLParser

from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.resolver import resolve
from readthedocs.core.unresolver import unresolve
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.utils import next_tag, recurse_while_none
from readthedocs.projects.models import Project
from readthedocs.storage import build_media_storage

log = logging.getLogger(__name__)


def escape_selector(selector):
    """Escape special characters from the section id."""
    regex = re.compile(r'(!|"|#|\$|%|\'|\(|\)|\*|\+|\,|\.|\/|\:|\;|\?|@)')
    ret = re.sub(regex, r'\\\1', selector)
    return ret


def clean_links(node, url):
    """
    Rewrite (internal) links to make them absolute.

    1. external links are not changed
    2. prepend URL to links that are just fragments (e.g. #section)
    3. prepend URL (without filename) to internal relative links
    """
    if url is None:
        return node

    for link in node.css('a'):
        base_url = urlparse(url)
        # We need to make all internal links, to be absolute
        href = link.attributes.get('href')
        if not href:
            continue

        parsed_href = urlparse(href)
        if parsed_href.scheme or parsed_href.path.startswith('/'):
            # TODO: replace absolute paths to a full URL.
            # Don't change absolute paths/URLs
            continue

        if not parsed_href.path and parsed_href.fragment:
            # href="#section-link"
            link.attrs['href'] = base_url.geturl() + href
        elif not base_url.path.endswith('/'):
            # internal relative link
            # href="../../another.html" and ``base_url`` is not HTMLDir
            # (e.g. /en/latest/deep/internal/section/page.html)
            # we want to remove the trailing filename (page.html) and use the rest as base URL
            # The resulting absolute link should be
            # https://slug.readthedocs.io/en/latest/deep/internal/section/../../another.html

            # remove the filename (page.html) from the original document URL (base_url) and,
            path, _ = base_url.path.rsplit('/', 1)
            # append the value of href (../../another.html) to the base URL.
            base_url = base_url._replace(path=path + '/')

        link.attrs['href'] = base_url.geturl() + href


class EmbedAPIBase(APIView):

    """
    Embed a section of content from any Read the Docs page.

    Returns headers and content that matches the queried section.

    ### Arguments

    We support two different ways to query this API:

        * project (required)
        * version (required)
        * doc
        * section
        * path

    or:

        * url (required)

    ### Example

        GET https://readthedocs.org/api/v2/embed/?project=requests&doc=index&section=User%20Guide&path=/index.html  # noqa

        GET https://readthedocs.org/api/v2/embed/?url=https://docs.readthedocs.io/en/latest/features.html%23github-bitbucket-and-gitlab-integration # noqa

    # Current Request
    """

    permission_classes = [IsAuthorizedToViewVersion]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    @functools.lru_cache(maxsize=1)
    def _get_project(self):
        if self.unresolved_url:
            project_slug = self.unresolved_url.project.slug
        else:
            project_slug = self.request.GET.get('project')
        return get_object_or_404(Project, slug=project_slug)

    @functools.lru_cache(maxsize=1)
    def _get_version(self):
        if self.unresolved_url:
            version_slug = self.unresolved_url.version_slug
        else:
            version_slug = self.request.GET.get('version', 'latest')
        project = self._get_project()
        return get_object_or_404(project.versions.all(), slug=version_slug)

    @cached_property
    def unresolved_url(self):
        url = self.request.GET.get('url')
        if not url:
            return None
        return unresolve(url)

    def get(self, request):
        """Handle the get request."""
        project = self._get_project()
        version = self._get_version()
        doc = request.GET.get('doc')
        section = request.GET.get('section')
        path = request.GET.get('path')
        url = request.GET.get('url')

        if self.unresolved_url:
            unresolved = self.unresolved_url
            project = unresolved.project
            path = unresolved.filename
            section = unresolved.fragment

            # update docpath from unresolved URL
            if path.endswith('/'):
                doc = doc.path.rstrip('/')
            else:
                doc = path.split('.html', 1)[0]

        # Check for None here becuase '' is valid for no filename
        if not project.slug and doc is not None:
            return Response(
                {
                    'error': (
                        'Invalid Arguments. '
                        'Please provide "project" and "doc", or "url" GET argument.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return do_embed(
            project=project,
            version=version,
            doc=doc,
            section=section,
            path=path,
            url=url,
        )


class EmbedAPI(SettingsOverrideObject):
    _default_class = EmbedAPIBase


def do_embed(*, project, version, doc=None, path=None, section=None, url=None):
    """Get the embed reponse from a document section."""
    if not url:
        external = version.type == EXTERNAL
        url = resolve(
            project=project,
            version_slug=version.slug,
            filename=path or doc,
            external=external,
        )

    content = None
    headers = None
    if version.is_sphinx_type:
        file_content = _get_doc_content(
            project=project,
            version=version,
            doc=doc,
        )
        content, headers, section = parse_sphinx(
            content=file_content,
            section=section,
            url=url,
        )
    else:
        # TODO: this should read from the html file itself,
        # we don't have fjson files for mkdocs.
        file_content = _get_doc_content(
            project=project,
            version=version,
            doc=doc,
        )
        content, headers, section = parse_mkdocs(
            content=file_content,
            section=section,
            url=url,
        )

    if content is None:
        return Response(
            {
                'error': (
                    "Can't find content for section: "
                    f"doc={doc} path={path} section={section}"
                )
            },
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'content': content,
        'headers': headers,
        'url': url,
        'meta': {
            'project': project.slug,
            'version': version.slug,
            'doc': doc,
            'section': section,
        },
    })


def _get_doc_content(project, version, doc):
    storage_path = project.get_storage_path(
        'json',
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    file_path = build_media_storage.join(
        storage_path,
        f'{doc}.fjson'.lstrip('/'),
    )
    try:
        with build_media_storage.open(file_path) as file:
            return json.load(file)
    except Exception:  # noqa
        log.warning('Unable to read file. file_path=%s', file_path)

    return None


def parse_sphinx(content, section, url):
    """Get the embed content for the section."""
    body = content.get('body')
    toc = content.get('toc')

    if not content or not body or not toc:
        return (None, None, section)

    headers = [
        recurse_while_none(element)
        for element in HTMLParser(toc).css('a')
    ]

    if not section and headers:
        # If no section is sent, return the content of the first one
        # TODO: This will always be the full page content,
        # lets do something smarter here
        section = list(headers[0].keys())[0].lower()

    if not section:
        return [], headers, None

    body_obj = HTMLParser(body)
    escaped_section = escape_selector(section)

    elements_id = [
        escaped_section,
        slugify(escaped_section),
        make_id(escaped_section),
        f'module-{escaped_section}',
    ]
    query_result = None
    for element_id in elements_id:
        if not element_id:
            continue
        query_result = body_obj.css_first(f'#{element_id}')
        if query_result:
            break

    if not query_result:
        selector = f'[header~={escaped_section}]'
        query_result = body_obj.css_first(selector)
        if query_result:
            query_result = query_result.parent

    # Handle ``dt`` special cases
    if query_result and query_result.tag == 'dt':
        parent = query_result.parent
        if 'glossary' in parent.attributes.get('class'):
            # Sphinx HTML structure for term glossary puts the ``id`` in the
            # ``dt`` element with the title of the term. In this case, we
            # need to return the next sibling which contains the definition
            # of the term itself.

            # Structure:
            # <dl class="glossary docutils">
            # <dt id="term-definition">definition</dt>
            # <dd>Text definition for the term</dd>
            # ...
            # </dl>
            query_result = next_tag(query_result)
        elif 'citation' in parent.attributes.get('class'):
            # Sphinx HTML structure for sphinxcontrib-bibtex puts the ``id`` in the
            # ``dt`` element with the title of the cite. In this case, we
            # need to return the next sibling which contains the cite itself.

            # Structure:
            # <dl class="citation">
            # <dt id="cite-id"><span><a>Title of the cite</a></span></dt>
            # <dd>Content of the cite</dd>
            # ...
            # </dl>
            query_result = next_tag(query_result)
        else:
            # Sphinx HTML structure for definition list puts the ``id``
            # the ``dt`` element, instead of the ``dl``. This makes
            # the backend to return just the title of the definition. If we
            # detect this case, we return the parent (the whole ``dl``)

            # Structure:
            # <dl class="confval">
            # <dt id="confval-config">
            # <code class="descname">config</code>
            # <a class="headerlink" href="#confval-config">¶</a></dt>
            # <dd><p>Text with a description</p></dd>
            # </dl>
            query_result = parent

    # Return the outer html for these elements
    if query_result and query_result.tag in ['span', 'h2'] and query_result.parent:
        query_result = query_result.parent

    section_html = []
    if query_result:
        clean_links(query_result, url)
        section_html = [query_result.html]

    return section_html, headers, section


def parse_mkdocs(content, section, url):  # pylint: disable=unused-argument
    """Get the embed content for the section."""
    ret = []
    headers = []
    return ret, headers, section
