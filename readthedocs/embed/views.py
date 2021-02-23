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
from pyquery import PyQuery as PQ  # noqa
from rest_framework import status
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.resolver import resolve
from readthedocs.core.unresolver import unresolve
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.utils import recurse_while_none
from readthedocs.projects.models import Project
from readthedocs.storage import build_media_storage

log = logging.getLogger(__name__)


def escape_selector(selector):
    """Escape special characters from the section id."""
    regex = re.compile(r'(!|"|#|\$|%|\'|\(|\)|\*|\+|\,|\.|\/|\:|\;|\?|@)')
    ret = re.sub(regex, r'\\\1', selector)
    return ret


def clean_links(obj, url):
    """
    Rewrite (internal) links to make them absolute.

    1. external links are not changed
    2. prepend URL to links that are just fragments (e.g. #section)
    3. prepend URL (without filename) to internal relative links
    """
    if url is None:
        return obj

    for link in obj.find('a'):
        base_url = urlparse(url)
        # We need to make all internal links, to be absolute
        href = link.attrib['href']
        parsed_href = urlparse(href)
        if parsed_href.scheme or parsed_href.path.startswith('/'):
            # don't change external links
            continue

        if not parsed_href.path and parsed_href.fragment:
            # href="#section-link"
            new_href = base_url.geturl() + href
            link.attrib['href'] = new_href
            continue

        if not base_url.path.endswith('/'):
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

        new_href = base_url.geturl() + href
        link.attrib['href'] = new_href

    return obj


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
        docpath = request.GET.get('path')
        url = request.GET.get('url')

        if self.unresolved_url:
            project, _, _, docpath, section = self.unresolved_url
            # update docpath from unresolved URL
            if docpath.endswith('/'):
                doc = doc.path.rstrip('/')
            else:
                doc = docpath.split('.html', 1)[0]

        # Check for None here becuase '' is valid for no filename
        if not project.slug and doc is not None:
            return Response({
                'error': (
                    'Invalid Arguments. '
                    'Please provide "project" and "doc", or "url" GET argument.'
                )
            },
                status=status.HTTP_400_BAD_REQUEST
            )

        return do_embed(
            project=project, version=version,
            doc=doc, section=section, path=docpath, url=url
        )


class EmbedAPI(SettingsOverrideObject):
    _default_class = EmbedAPIBase


def do_embed(project, version, doc, section=None, path=None, url=None):
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
    fjson_content = _get_doc_content(project, version, doc)
    if fjson_content:
        content, headers, section = parse_sphinx(fjson_content, section, url)
        if content is None:
            content, headers, section = parse_mkdocs(fjson_content, section, url)

    if content is None:
        return Response(
            {'error': f"Can't find JSON document: {doc}"},
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
    file_path = build_media_storage.join(storage_path, f'{doc}.fjson')
    try:
        with build_media_storage.open(file_path) as file:
            file_contents = file.read()
            return json.loads(file_contents)
    except Exception:  # noqa
        log.warning('Unable to read file: %s', file_path)

    return None


def parse_sphinx(content, section, url):
    """Get the embed content for the section."""
    ret = []
    headers = []

    if not content or not content.get('body') or not content.get('toc'):
        return (None, None, section)

    body = content['body']
    toc = content['toc']
    for element in PQ(toc)('a'):
        headers.append(recurse_while_none(element))

    if not section and headers:
        # If no section is sent, return the content of the first one
        # TODO: This will always be the full page content,
        # lets do something smarter here
        section = list(headers[0].keys())[0].lower()

    if section:
        body_obj = PQ(body)
        body_obj = clean_links(body_obj, url)

        escaped_section = escape_selector(section)

        query = '#module-' + escaped_section
        query_obj = body_obj(str(query))

        if not query_obj:
            query = '#' + slugify(escaped_section)
            query_obj = body_obj(str(query))

        if not query_obj:
            query = '#' + make_id(escaped_section)
            if query != '#':
                query_obj = body_obj(str(query))

        if not query_obj:
            query = '#' + escaped_section
            query_obj = body_obj(str(query))

        if not query_obj:
            query_obj = body_obj(':header:contains("{title}")'.format(
                title=str(escaped_section))).parent()

        # Handle ``dt`` special cases
        if len(query_obj) == 1 and query_obj[0].tag == 'dt':
            parent = query_obj.parent()
            if 'glossary' in parent.attr('class'):
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
                query_obj = query_obj.next()
            elif 'citation' in parent.attr('class'):
                # Sphinx HTML structure for sphinxcontrib-bibtex puts the ``id`` in the
                # ``dt`` element with the title of the cite. In this case, we
                # need to return the next sibling which contains the cite itself.

                # Structure:
                # <dl class="citation">
                # <dt id="cite-id"><span><a>Title of the cite</a></span></dt>
                # <dd>Content of the cite</dd>
                # ...
                # </dl>
                query_obj = query_obj.next()
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
                query_obj = parent

        def dump(obj):
            """Handle API-based doc HTML."""
            if obj[0].tag in ['span', 'h2']:
                return obj.parent().outerHtml()
            return obj.outerHtml()

        for obj in query_obj:
            ret.append(dump(PQ(obj)))
    return (ret, headers, section)


def parse_mkdocs(content, section, url):  # pylint: disable=unused-argument
    """Get the embed content for the section."""
    ret = []
    headers = []

    if not content or not content.get('content'):
        return (None, None, section)

    body = content['content']
    for element in PQ(body)('h2'):
        headers.append(recurse_while_none(element))

    if not section and headers:
        # If no section is sent, return the content of the first one
        section = list(headers[0].keys())[0].lower()

    if section:
        body_obj = PQ(body)
        escaped_section = escape_selector(section)
        section_list = body_obj(
            ':header:contains("{title}")'.format(title=str(escaped_section)))
        for num in range(len(section_list)):
            header2 = section_list.eq(num)
            # h2_title = h2.text().strip()
            # section_id = h2.attr('id')
            h2_content = ""
            next_p = header2.next()
            while next_p:
                if next_p[0].tag == 'h2':
                    break
                h2_html = next_p.outerHtml()
                if h2_html:
                    h2_content += "\n%s\n" % h2_html
                next_p = next_p.next()
            if h2_content:
                ret.append(h2_content)
                # ret.append({
                #     'id': section_id,
                #     'title': h2_title,
                #     'content': h2_content,
                # })
    return (ret, headers, section)
