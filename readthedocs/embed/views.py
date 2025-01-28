"""Views for the embed app."""
import datetime
import json
import re

import pytz
import structlog
from django.conf import settings
from django.template.defaultfilters import slugify
from docutils.nodes import make_id
from pyquery import PyQuery as PQ  # noqa
from rest_framework import status
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.mixins import CDNCacheTagsMixin, EmbedAPIMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.api.v3.permissions import HasEmbedAPIAccess
from readthedocs.core.resolver import Resolver
from readthedocs.embed.utils import clean_references, recurse_while_none
from readthedocs.storage import build_media_storage

log = structlog.get_logger(__name__)


def escape_selector(selector):
    """Escape special characters from the section id."""
    regex = re.compile(r'(!|"|#|\$|%|\'|\(|\)|\*|\+|\,|\.|\/|\:|\;|\?|@)')
    ret = re.sub(regex, r"\\\1", selector)
    return ret


class EmbedAPI(EmbedAPIMixin, CDNCacheTagsMixin, APIView):
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

    permission_classes = [HasEmbedAPIAccess, IsAuthorizedToViewVersion]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    @property
    def external(self):
        # Always return False because APIv2 does not support external domains
        return False

    def _is_disabled_for_deprecation(self):
        if not settings.RTD_ENFORCE_BROWNOUTS_FOR_DEPRECATIONS:
            return False

        tzinfo = pytz.timezone("America/Los_Angeles")
        now = datetime.datetime.now(tz=tzinfo)
        # Dates as per https://about.readthedocs.com/blog/2024/11/embed-api-v2-deprecated/.
        # fmt: off
        is_disabled = (
            # 12 hours brownout.
            datetime.datetime(2024, 12, 9, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2024, 12, 9, 12, 0, 0, tzinfo=tzinfo)
            # 24 hours brownout.
            or datetime.datetime(2025, 1, 13, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=tzinfo)
            # Permanent removal.
            or datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=tzinfo) < now
        )
        # fmt: on
        return is_disabled

    def get(self, request):
        """Handle the get request."""

        if self._is_disabled_for_deprecation():
            return Response(
                {
                    "error": (
                        "Embed API v2 has been deprecated and is no longer available, please use embed API v3 instead. "
                        "Read our blog post for more information: https://about.readthedocs.com/blog/2024/11/embed-api-v2-deprecated/."
                    )
                },
                status=status.HTTP_410_GONE,
            )

        project = self._get_project()
        version = self._get_version()

        url = request.GET.get("url")
        path = request.GET.get("path", "")
        doc = request.GET.get("doc")
        section = request.GET.get("section")

        if url:
            unresolved = self.unresolved_url
            path = unresolved.filename
            section = unresolved.parsed_url.fragment
        elif not path and not doc:
            return Response(
                {
                    "error": (
                        "Invalid Arguments. "
                        'Please provide "url" or "section" and "path" GET arguments.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate the docname from path
        # by removing the ``.html`` extension and trailing ``/``.
        if path:
            doc = re.sub(r"(.+)\.html$", r"\1", path.strip("/"))

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
                    "error": (
                        "Can't find content for section: "
                        f"doc={doc} path={path} section={section}"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        log.info(
            "EmbedAPI successful response.",
            project_slug=project.slug,
            version_slug=version.slug,
            doc=doc,
            section=section,
            path=path,
            url=url,
            referer=request.headers.get("Referer"),
            hoverxref_version=request.headers.get("X-Hoverxref-Version"),
        )
        return Response(response)


def do_embed(*, project, version, doc=None, path=None, section=None, url=None):
    """Get the embed response from a document section."""
    if not url:
        url = Resolver().resolve_version(
            project=project,
            version=version,
            filename=path or doc,
        )

    content = None
    headers = None
    # Embed API v2 supports Sphinx only.
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
        log.info("Using EmbedAPIv2 for a non Sphinx project.")
        return None

    if content is None:
        return None

    return {
        "content": content,
        "headers": headers,
        "url": url,
        "meta": {
            "project": project.slug,
            "version": version.slug,
            "doc": doc,
            "section": section,
        },
    }


def _get_doc_content(project, version, doc):
    storage_path = project.get_storage_path(
        "json",
        version_slug=version.slug,
        include_file=False,
        version_type=version.type,
    )
    file_path = build_media_storage.join(
        storage_path,
        f"{doc}.fjson".lstrip("/"),
    )
    try:
        with build_media_storage.open(file_path) as file:
            return json.load(file)
    except Exception:  # noqa
        log.warning("Unable to read file.", file_path=file_path)

    return None


def parse_sphinx(content, section, url):
    """Get the embed content for the section."""
    body = content.get("body")
    toc = content.get("toc")

    if not content or not body or not toc:
        return (None, None, section)

    headers = [recurse_while_none(element) for element in PQ(toc)("a")]

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
        f"module-{escaped_section}",
    ]
    query_result = []
    for element_id in elements_id:
        if not element_id:
            continue
        try:
            query_result = body_obj(f"#{element_id}")
            if query_result:
                break
        except Exception:  # noqa
            log.info(
                "Failed to query section.",
                url=url,
                element_id=element_id,
            )

    if not query_result:
        selector = f':header:contains("{escaped_section}")'
        query_result = body_obj(selector).parent()

    # Handle ``dt`` special cases
    if len(query_result) == 1 and query_result[0].tag == "dt":
        parent = query_result.parent()
        if "glossary" in parent.attr("class"):
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
        elif "citation" in parent.attr("class"):
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
        if obj[0].tag in ["span", "h2"]:
            return obj.parent().outerHtml()
        return obj.outerHtml()

    ret = [dump(clean_references(obj, url)) for obj in query_result]
    return ret, headers, section
