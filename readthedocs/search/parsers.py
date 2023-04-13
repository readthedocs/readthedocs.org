"""JSON/HTML parsers for search indexing."""

import itertools
import os
import re
from urllib.parse import urlparse

import orjson as json
import structlog
from selectolax.parser import HTMLParser

from readthedocs.storage import build_media_storage

log = structlog.get_logger(__name__)


class GenericParser:

    # Limit that matches the ``index.mapping.nested_objects.limit`` ES setting.
    max_inner_documents = 10000

    def __init__(self, version):
        self.version = version
        self.project = self.version.project
        self.storage = build_media_storage

    def _get_page_content(self, page):
        """Gets the page content from storage."""
        content = None
        try:
            storage_path = self.project.get_storage_path(
                type_='html',
                version_slug=self.version.slug,
                include_file=False,
            )
            file_path = self.storage.join(storage_path, page)
            with self.storage.open(file_path, mode='r') as f:
                content = f.read()
        except Exception:
            log.warning(
                'Unhandled exception during search processing file.',
                page=page,
            )
        return content

    def _get_page_title(self, body, html):
        """
        Gets the title from the html page.

        The title is the first section in the document,
        falling back to the ``title`` tag.
        """
        first_header = body.css_first('h1')
        if first_header:
            title, _ = self._parse_section_title(first_header)
            return title

        title = html.css_first('title')
        if title:
            return self._parse_content(title.text())

        return None

    def _get_main_node(self, html):
        """
        Gets the main node from where to start indexing content.

        The main node is tested in the following order:

        - Try with a tag with the ``main`` role.
          This role is used by several static sites and themes.
        - Try the ``main`` tag.
        - Try the first ``h1`` node and return its parent
          Usually all sections are neighbors,
          so they are children of the same parent node.
        - Return the body element itself if all checks above fail.
        """
        body = html.body
        main_node = body.css_first('[role=main]')
        if main_node:
            return main_node

        main_node = body.css_first('main')
        if main_node:
            return main_node

        # TODO: this could be done in smarter way,
        # checking for common parents between all h nodes.
        first_header = body.css_first("h1")
        if first_header:
            return self._get_header_container(first_header).parent

        return body

    def _get_header_container(self, h_tag):
        """
        Get the *real* container of a header tag or title.

        If the parent of the ``h`` tag is a ``header`` tag,
        then we return the ``header`` tag,
        since the header tag acts as a container for the title of the section.
        Otherwise, we return the tag itself.
        """
        if h_tag.parent.tag == "header":
            return h_tag.parent
        return h_tag

    def _parse_content(self, content):
        """Converts all new line characters and multiple spaces to a single space."""
        content = content.strip().split()
        content = (text.strip() for text in content)
        content = ' '.join(text for text in content if text)
        return content

    def _parse_sections(self, title, body):
        """
        Parses each section into a structured dict.

        Sub-sections are nested, so they are children of the outer section,
        and sections with the same level are neighbors.
        We index the content under a section till before the next one.

        We can have pages that have content before the first title or that don't have a title,
        we index that content first under the title of the original page.
        """

        document_title = title

        indexed_nodes = []

        for dd, dt, section in self._parse_dls(body):
            indexed_nodes.append(dd)
            indexed_nodes.append(dt)
            yield section

        # Remove all seen and indexed data outside of traversal.
        # We want to avoid modifying the DOM tree while traversing it.
        for node in indexed_nodes:
            node.decompose()

        # Index content for pages that don't start with a title.
        # We check for sections till 3 levels to avoid indexing all the content
        # in this step.
        try:
            content, _ = self._parse_section_content(
                body.child,
                depth=3,
            )
            if content:
                yield {
                    "id": "",
                    "title": document_title,
                    "content": content,
                }
        except Exception as e:
            log.info("Unable to index section", section=str(e))

        # Index content from h1 to h6 headers.
        for section in [body.css(f"h{h}") for h in range(1, 7)]:
            for tag in section:
                try:
                    title, _id = self._parse_section_title(tag)
                    next_tag = self._get_header_container(tag).next
                    content, _ = self._parse_section_content(next_tag, depth=2)
                    yield {
                        "id": _id,
                        "title": title,
                        "content": content,
                    }
                except Exception:
                    log.info("Unable to index section.", exc_info=True)

    def _parse_dls(self, body):

        # All terms in <dl>s are treated as sections.
        # We traverse by <dl> - traversing by <dt> has shown in experiments to render a
        # different traversal order, which could make the tests more unstable.
        dls = body.css("dl")

        for dl in dls:

            # Hack: Since we cannot use '> dt' nor ':host' in selectolax/Modest,
            # we use an iterator to select immediate descendants.
            dts = (node for node in dl.iter() if node.tag == "dt" and node.id)

            # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dt
            # multiple <dt> elements in a row indicate several terms that are
            # all defined by the immediate next <dd> element.
            for dt in dts:
                title, _id = self._parse_dt(dt)
                # Select the first adjacent <dd> using a "gamble" that seems to work.
                # In this example, we cannot use the current <dt>'s ID because they contain invalid
                # CSS selector syntax and there's no apparent way to fix that.
                # https://developer.mozilla.org/en-US/docs/Web/CSS/General_sibling_combinator
                dd = dt.css_first("dt ~ dd")

                # We only index a dt with an id attribute and an accompanying dd
                if not dd or not _id:
                    continue

                # Create a copy of the node to avoid manipulating the
                # data structure that we're iterating over
                dd_copy = HTMLParser(dd.html).body.child

                # Remove all nested domains from dd_copy.
                # They are already parsed separately.
                for node in dd_copy.css("dl"):
                    # Traverse all <dt>s with an ID (the ones we index!)
                    for _dt in node.css('dt[id]:not([id=""])'):
                        # Fetch adjacent <dd>s and remove them
                        _dd_dt = _dt.css_first("dt ~ dd")
                        if _dd_dt:
                            _dd_dt.decompose()
                        # Remove the <dt> too
                        _dt.decompose()

                # The content of the <dt> section is the content of the accompanying <dd>
                content = self._parse_content(dd_copy.text())

                yield (
                    dd,
                    dt,
                    {
                        "id": _id,
                        "title": title,
                        "content": content,
                    },
                )

    def _parse_dt(self, tag):
        """
        Parses a definition term <dt>.

        If the <dt> does not have an id attribute, it cannot be referenced.
        This should be understood by the caller.
        """
        section_id = tag.attributes.get("id", "")
        return self._parse_content(tag.text()), section_id

    def _get_sections(self, title, body):
        """Get the first `self.max_inner_documents` sections."""
        iterator = self._parse_sections(title=title, body=body)
        sections = list(itertools.islice(iterator, 0, self.max_inner_documents))
        try:
            next(iterator)
        except StopIteration:
            pass
        else:
            log.warning(
                'Limit of inner sections exceeded.',
                project_slug=self.project.slug,
                version_slug=self.version.slug,
                limit=self.max_inner_documents,
            )
        return sections

    def _clean_body(self, body):
        """
        Removes nodes with irrelevant content before parsing its sections.

        This method is documented here:
        https://dev.readthedocs.io/page/search-integration.html#irrelevant-content

        .. warning::

           This will mutate the original `body`.
        """
        nodes_to_be_removed = itertools.chain(
            # Navigation nodes
            body.css('nav'),
            body.css('[role=navigation]'),
            body.css('[role=search]'),
            # Permalinks
            body.css('.headerlink'),
            # Line numbers from code blocks, they are very noisy in contents.
            # This convention is popular in Sphinx.
            body.css(".linenos"),
            body.css(".lineno"),
        )
        for node in nodes_to_be_removed:
            node.decompose()

        return body

    def _is_section(self, tag):
        """
        Check if `tag` is a section (linkeable header).

        The tag is a section if it's a ``h`` or a ``header`` tag.
        """
        is_h_tag = re.match(r"h\d$", tag.tag)
        return is_h_tag or tag.tag == "header"

    def _parse_section_title(self, tag):
        """
        Parses a section title tag and gets its id.

        The id (used to link to the section) is tested in the following order:

        - Get the id from the node itself.
        - Get the id from the parent node.
        """
        section_id = tag.attributes.get('id', '')
        if not section_id:
            parent = tag.parent
            section_id = parent.attributes.get('id', '')

        return self._parse_content(tag.text()), section_id

    def _parse_section_content(self, tag, *, depth=0):
        """
        Gets the content from tag till before a new section.

        if depth > 0, recursively check for sections in all tag's children.

        Returns a tuple with: the parsed content,
        and a boolean indicating if a section was found.
        """
        contents = []
        section_found = False

        next_tag = tag
        while next_tag:
            if section_found or self._is_section(next_tag):
                section_found = True
                break

            if self._is_code_section(next_tag):
                content = self._parse_code_section(next_tag)
            elif depth <= 0 or not next_tag.child:
                # Calling .text() with deep `True` over a text node will return empty.
                deep = next_tag.tag != '-text'
                content = next_tag.text(deep=deep)
            else:
                content, section_found = self._parse_section_content(
                    tag=next_tag.child,
                    depth=depth - 1
                )

            if content:
                contents.append(content)
            next_tag = next_tag.next

        return self._parse_content("".join(contents)), section_found

    def _is_code_section(self, tag):
        """
        Check if `tag` is a code section.

        Sphinx and Mkdocs codeblocks usually have a class named
        ``highlight`` or ``highlight-{language}``.
        """
        if not tag.css_first('pre'):
            return False

        for c in tag.attributes.get('class', '').split():
            if c.startswith('highlight'):
                return True
        return False

    def _parse_code_section(self, tag):
        """
        Parse a code section to fetch relevant content only.

        - Removes line numbers.

        Sphinx and Mkdocs may use a table when the code block includes line numbers.
        This table has a td tag with a ``lineos`` class.
        Other implementations put the line number within the code,
        inside span tags with the ``lineno`` class.
        """
        nodes_to_be_removed = itertools.chain(tag.css('.linenos'), tag.css('.lineno'))
        for node in nodes_to_be_removed:
            node.decompose()

        contents = []
        for node in tag.css('pre'):
            # XXX: Don't call to `_parse_content`
            # if we decide to show code results more nicely,
            # so the indentation isn't lost.
            content = node.text().strip('\n')
            contents.append(self._parse_content(content))
        return ' '.join(contents)

    def parse(self, page):
        """
        Get the parsed JSON for search indexing.

        Returns a dictionary with the following structure.
        {
            'path': 'file path',
            'title': 'Title',
            'sections': [
                {
                    'id': 'section-anchor',
                    'title': 'Section title',
                    'content': 'Section content',
                },
            ],
            'domain_data': {},
        }
        """
        try:
            content = self._get_page_content(page)
            if content:
                return self._process_content(page, content)
        except Exception:
            log.info("Failed to index page.", path=page, exc_info=True)
        return {
            "path": page,
            "title": "",
            "sections": [],
            "domain_data": {},
        }

    def _process_content(self, page, content):
        """Parses the content into a structured dict."""
        html = HTMLParser(content)
        body = self._get_main_node(html)
        title = ""
        sections = []
        if body:
            body = self._clean_body(body)
            title = self._get_page_title(body, html) or page
            sections = self._get_sections(title=title, body=body)
        else:
            log.info(
                "Page doesn't look like it has valid content, skipping.",
                page=page,
            )
        return {
            "path": page,
            "title": title,
            "sections": sections,
            "domain_data": {},
        }


class SphinxParser(GenericParser):

    """
    Parser for Sphinx generated html pages.

    This parser relies on the fjson file generated by Sphinx.
    It checks for two paths for each html file,
    this is because the HTMLDir builder can generate the same html file from two different places:

    - foo.rst
    - foo/index.rst

    Both lead to foo/index.html.
    """

    def parse(self, page):
        basename = os.path.splitext(page)[0]
        fjson_paths = [f'{basename}.fjson']
        if basename.endswith('/index'):
            new_basename = re.sub(r'\/index$', '', basename)
            fjson_paths.append(f'{new_basename}.fjson')

        storage_path = self.project.get_storage_path(
            type_='json',
            version_slug=self.version.slug,
            include_file=False,
        )

        for fjson_path in fjson_paths:
            try:
                fjson_path = self.storage.join(storage_path, fjson_path)
                if self.storage.exists(fjson_path):
                    return self._process_fjson(fjson_path)
            except Exception:
                log.warning(
                    'Unhandled exception during search processing file.',
                    path=fjson_path,
                )

        return {
            'path': page,
            'title': '',
            'sections': [],
            'domain_data': {},
        }

    def _process_fjson(self, fjson_path):
        """Reads the fjson file from storage and parses it into a structured dict."""
        try:
            with self.storage.open(fjson_path, mode='r') as f:
                file_contents = f.read()
        except IOError:
            log.info('Unable to read file.', path=fjson_path)
            raise

        data = json.loads(file_contents)
        sections = []
        path = ''
        title = ''

        if 'current_page_name' in data:
            path = data['current_page_name']
        else:
            log.info('Unable to index file due to no name.', path=fjson_path)

        if 'title' in data:
            title = data['title']
            title = HTMLParser(title).text().strip()
        else:
            log.info('Unable to index title.', path=fjson_path)

        if 'body' in data:
            try:
                body = self._clean_body(HTMLParser(data["body"]))
                sections = self._get_sections(title=title, body=body.body)
            except Exception as e:
                log.info("Unable to index sections.", path=fjson_path, exception=e)
        else:
            log.info('Unable to index content.', path=fjson_path)

        return {
            "path": path,
            "title": title,
            "sections": sections,
            "domain_data": {},  # deprecated
        }

    def _clean_body(self, body):
        """
        Removes nodes in Sphinx-generated HTML structures.

        This method is overridden to remove contents that are likely
        to be useless for search indexing.

        Currently: TOC elements.
        """
        body = super()._clean_body(body)

        # TODO: see if we really need to remove TOC elements like below?
        # benjaoming: I didn't see this in sphinx-rtd-theme, however since it wraps the menu in
        # a <nav>, it's already covered. I didn't see this match local table of contents, neither
        # and they are also wrapped in a <nav> so covered by _clean_body as well.
        nodes_to_be_removed = itertools.chain(
            body.css(".toctree-wrapper"),
            body.css(".contents.local.topic"),
        )

        # removing all nodes in list
        for node in nodes_to_be_removed:
            node.decompose()

        return body


class MkDocsParser(GenericParser):

    """
    MkDocs parser.

    Index using the json index file instead of the html content.
    """

    def parse(self, page):
        storage_path = self.project.get_storage_path(
            type_='html',
            version_slug=self.version.slug,
            include_file=False,
        )
        try:
            file_path = self.storage.join(storage_path, 'search/search_index.json')
            if self.storage.exists(file_path):
                index_data = self._process_index_file(file_path, page=page)
                if index_data:
                    return index_data
        except Exception:
            log.warning(
                'Unhandled exception during search processing file.',
                page=page,
            )
        return {
            'path': page,
            'title': '',
            'sections': [],
            'domain_data': {},
        }

    def _process_index_file(self, json_path, page):
        """Reads the json index file and parses it into a structured dict."""
        try:
            with self.storage.open(json_path, mode='r') as f:
                file_contents = f.read()
        except IOError:
            log.info('Unable to read file.', path=json_path)
            raise

        data = json.loads(file_contents)
        page_data = {}

        for section in data.get('docs', []):
            parsed_path = urlparse(section.get('location', ''))
            fragment = parsed_path.fragment
            path = parsed_path.path

            # Some old versions of mkdocs
            # index the pages as ``/page.html`` instead of ``page.html``.
            path = path.lstrip('/')

            if path == '' or path.endswith('/'):
                path += 'index.html'

            if page != path:
                continue

            title = self._parse_content(
                HTMLParser(section.get('title')).text()
            )
            content = self._parse_content(
                HTMLParser(section.get('text')).text()
            )

            # If it doesn't have a fragment,
            # it means is the page itself.
            if not fragment:
                page_data.update({
                    'path': path,
                    'title': title,
                    'domain_data': {},
                })
            # Content without a fragment need to be indexed as well,
            # this happens when the page doesn't start with a header,
            # or if it doesn't contain any headers at all.
            page_data.setdefault('sections', []).append({
                'id': fragment,
                'title': title,
                'content': content,
            })

        return page_data
