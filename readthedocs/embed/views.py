"""Views for the embed app."""

import json
import re

import structlog
from django.template.defaultfilters import slugify
from docutils.nodes import make_id
from pyquery import PyQuery as PQ  # noqa
from rest_framework import status
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.mixins import CDNCacheTagsMixin, EmbedAPIMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.resolver import resolve
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.embed.utils import clean_links, recurse_while_none
from readthedocs.storage import build_media_storage

log = structlog.get_logger(__name__)


def escape_selector(selector):
    """Escape special characters from the section id."""
    regex = re.compile(r'(!|"|#|\$|%|\'|\(|\)|\*|\+|\,|\.|\/|\:|\;|\?|@)')
    ret = re.sub(regex, r'\\\1', selector)
    return ret


class EmbedAPIBase(EmbedAPIMixin, CDNCacheTagsMixin, APIView):

    # pylint: disable=line-too-long

    """
    Embed a section of content from any Read the Docs page.

    Returns headers and content that matches the queried section.

    ### Arguments

    We support two different ways to query the API:

    * project (required)
    * version (required)
    * doc or path (required)
    * section

    or:

    * url (with fragment) (required)

    ### Example

    - GET https://readthedocs.org/api/v2/embed/?project=requestsF&version=latest&doc=index&section=User%20Guide&path=/index.html
    - GET https://readthedocs.org/api/v2/embed/?url=https://docs.readthedocs.io/en/latest/features.html%23github-bitbucket-and-gitlab-integration

    # Current Request
    """  # noqa

    permission_classes = [IsAuthorizedToViewVersion]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    @property
    def external(self):
        # Always return False because APIv2 does not support external domains
        return False

    def get(self, request):
        """Handle the get request."""
        project = self._get_project()
        version = self._get_version()

        url = request.GET.get('url')
        path = request.GET.get('path', '')
        doc = request.GET.get('doc')
        section = request.GET.get('section')

        if url:
            unresolved = self.unresolved_url
            path = unresolved.filename
            section = unresolved.fragment
        elif not path and not doc:
            return Response(
                {
                    'error': (
                        'Invalid Arguments. '
                        'Please provide "url" or "section" and "path" GET arguments.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate the docname from path
        # by removing the ``.html`` extension and trailing ``/``.
        if path:
            doc = re.sub(r'(.+)\.html$', r'\1', path.strip('/'))

        response = do_embed(
            project=project,
            version=version,
            doc=doc,
            section=section,
            path=path,
            url=url,
        )

        if not response:
            return Response(
                {
                    'error': (
                        "Can't find content for section: "
                        f"doc={doc} path={path} section={section}"
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        log.info(
            'EmbedAPI successful response.',
            project_slug=project.slug,
            version_slug=version.slug,
            doc=doc,
            section=section,
            path=path,
            url=url,
            referer=request.META.get('HTTP_REFERER'),
            hoverxref_version=request.META.get('HTTP_X_HOVERXREF_VERSION'),
        )
        return Response(response)


class EmbedAPI(SettingsOverrideObject):
    _default_class = EmbedAPIBase


def do_embed(*, project, version, doc=None, path=None, section=None, url=None):
    """Get the embed response from a document section."""
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
        if not file_content:
            return None

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
        return None

    return {
        'content': content,
        'headers': headers,
        'url': url,
        'meta': {
            'project': project.slug,
            'version': version.slug,
            'doc': doc,
            'section': section,
        },
    }


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
        log.warning('Unable to read file.', file_path=file_path)

    return None


def parse_sphinx(content, section, url):
    """Get the embed content for the section."""
    body = content.get('body')
    toc = content.get('toc')

    if not content or not body or not toc:
        return (None, None, section)

    headers = [
        recurse_while_none(element)
        for element in PQ(toc)('a')
    ]

    if not section and headers:
        # If no section is sent, return the content of the first one
        # TODO: This will always be the full page content,
        # lets do something smarter here
        section = list(headers[0].keys())[0].lower()

    if not section:
        return [], headers, None

    body_obj = PQ(body)
    escaped_section = escape_selector(section)

    elements_id = [
        escaped_section,
        slugify(escaped_section),
        make_id(escaped_section),
        f'module-{escaped_section}',
    ]
    query_result = []
    for element_id in elements_id:
        if not element_id:
            continue
        try:
            query_result = body_obj(f'#{element_id}')
            if query_result:
                break
        except Exception:  # noqa
            log.info(
                'Failed to query section.',
                url=url,
                element_id=element_id,
            )

    if not query_result:
        selector = f':header:contains("{escaped_section}")'
        query_result = body_obj(selector).parent()

    # Handle ``dt`` special cases
    if len(query_result) == 1 and query_result[0].tag == 'dt':
        parent = query_result.parent()
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
            query_result = query_result.next()
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
            query_result = query_result.next()
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

    def dump(obj):
        """Handle API-based doc HTML."""
        if obj[0].tag in ['span', 'h2']:
            return obj.parent().outerHtml()
        return obj.outerHtml()

    ret = [
        dump(clean_links(obj, url))
        for obj in query_result
    ]
    return ret, headers, section


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
