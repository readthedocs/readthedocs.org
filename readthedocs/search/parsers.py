"""JSON/HTML parsers for search indexing."""

import itertools
import logging
import os
import re
from urllib.parse import urlparse

import orjson as json
from django.conf import settings
from django.core.files.storage import get_storage_class
from selectolax.parser import HTMLParser

log = logging.getLogger(__name__)


class BaseParser:

    def __init__(self, version):
        self.version = version
        self.project = self.version.project
        self.storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

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
                'Unhandled exception during search processing file: %s',
                page,
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
        first_header = body.css_first('h1')
        if first_header:
            return first_header.parent

        return None

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
        body = self._clean_body(body)

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
                    'id': '',
                    'title': title,
                    'content': content,
                }
        except Exception as e:
            log.info('Unable to index section: %s', str(e))

        # Index content from h1 to h6 headers.
        for head_level in range(1, 7):
            tags = body.css(f'h{head_level}')
            for tag in tags:
                try:
                    title, id = self._parse_section_title(tag)
                    content, _ = self._parse_section_content(tag.next, depth=2)
                    yield {
                        'id': id,
                        'title': title,
                        'content': content,
                    }
                except Exception as e:
                    log.info('Unable to index section: %s', str(e))

    def _clean_body(self, body):
        """
        Removes nodes with irrelevant content before parsing its sections.

        .. warning::

           This will mutate the original `body`.
        """
        # Remove all navigation nodes
        nodes_to_be_removed = itertools.chain(
            body.css('nav'),
            body.css('[role=navigation]'),
            body.css('[role=search]'),
        )
        for node in nodes_to_be_removed:
            node.decompose()

        return body

    def _is_section(self, tag):
        """
        Check if `tag` is a section (linkeable header).

        The tag is a section if it's a ``h`` tag.
        """
        is_header_tag = re.match(r'h\d$', tag.tag)
        return is_header_tag

    def _parse_section_title(self, tag):
        """
        Parses a section title tag and gets its id.

        The id (used to link to the section) is tested in the following order:

        - Get the id from the node itself.
        - Get the id from the parent node.

        Additionally:

        - Removes permalink values
        """
        nodes_to_be_removed = tag.css('.headerlink')
        for node in nodes_to_be_removed:
            node.decompose()

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

        return self._parse_content(''.join(contents)), section_found

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
        raise NotImplementedError


class SphinxParser(BaseParser):

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
                    'Unhandled exception during search processing file: %s',
                    fjson_path,
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
            log.info('Unable to read file: %s', fjson_path)
            raise

        data = json.loads(file_contents)
        sections = []
        path = ''
        title = ''
        domain_data = {}

        if 'current_page_name' in data:
            path = data['current_page_name']
        else:
            log.info('Unable to index file due to no name %s', fjson_path)

        if 'title' in data:
            title = data['title']
            title = HTMLParser(title).text().strip()
        else:
            log.info('Unable to index title for: %s', fjson_path)

        if 'body' in data:
            try:
                body = HTMLParser(data['body'])
                sections = list(self._parse_sections(title=title, body=body.body))
            except Exception as e:
                log.info('Unable to index sections for: %s', fjson_path)

            try:
                # Create a new html object, since the previous one could have been modified.
                body = HTMLParser(data['body'])
                domain_data = self._generate_domains_data(body)
            except Exception as e:
                log.info('Unable to index domains for: %s', fjson_path)
        else:
            log.info('Unable to index content for: %s', fjson_path)

        return {
            'path': path,
            'title': title,
            'sections': sections,
            'domain_data': domain_data,
        }

    def _clean_body(self, body):
        """
        Removes sphinx domain nodes.

        This method is overriden to remove contents that are likely
        to be a sphinx domain (`dl` tags).
        We already index those in another step.
        """
        body = super()._clean_body(body)

        nodes_to_be_removed = []

        # remove all <dl> tags which contains <dt> tags having 'id' attribute
        dt_tags = body.css('dt[id]')
        for tag in dt_tags:
            parent = tag.parent
            if parent.tag == 'dl':
                nodes_to_be_removed.append(parent)

        # TODO: see if we really need to remove these
        # remove `Table of Contents` elements
        nodes_to_be_removed += body.css('.toctree-wrapper') + body.css('.contents.local.topic')

        # removing all nodes in list
        for node in nodes_to_be_removed:
            node.decompose()

        return body

    def _generate_domains_data(self, body):
        """
        Generate sphinx domain objects' docstrings.

        Returns a dict with the generated data.
        The returned dict is in the following form::

            {
                "domain-id-1": "docstrings for the domain-id-1",
                "domain-id-2": "docstrings for the domain-id-2",
            }
        """

        domain_data = {}
        dl_tags = body.css('dl')

        for dl_tag in dl_tags:

            dt = dl_tag.css('dt')
            dd = dl_tag.css('dd')

            # len(dt) should be equal to len(dd)
            # because these tags go together.
            for title, desc in zip(dt, dd):
                try:
                    id_ = title.attributes.get('id', '')
                    if id_:
                        docstrings = self._parse_domain_tag(desc)
                        domain_data[id_] = docstrings
                except Exception:
                    log.exception('Error parsing docstring for domains')

        return domain_data

    def _parse_domain_tag(self, tag):
        """Returns the text from the description tag of the domain."""

        # remove the 'dl', 'dt' and 'dd' tags from it
        # because all the 'dd' and 'dt' tags are inside 'dl'
        # and all 'dl' tags are already captured.
        nodes_to_be_removed = tag.css('dl') + tag.css('dt') + tag.css('dd')
        for node in nodes_to_be_removed:
            node.decompose()

        docstring = self._parse_content(tag.text())
        return docstring


class MkDocsParser(BaseParser):

    """
    MkDocs parser.

    Index from the json index file or directly from the html content.
    """

    def parse(self, page):
        # Avoid circular import
        from readthedocs.projects.models import Feature
        if self.project.has_feature(Feature.INDEX_FROM_HTML_FILES):
            return self.parse_from_html(page)
        return self.parse_from_index_file(page)

    def parse_from_html(self, page):
        try:
            content = self._get_page_content(page)
            if content:
                return self._process_content(page, content)
        except Exception as e:
            log.info('Failed to index page %s, %s', page, str(e))
        return {
            'path': page,
            'title': '',
            'sections': [],
            'domain_data': {},
        }

    def _process_content(self, page, content):
        """Parses the content into a structured dict."""
        html = HTMLParser(content)
        body = self._get_main_node(html)
        title = ""
        sections = []
        if body:
            title = self._get_page_title(body, html) or page
            sections = list(self._parse_sections(title, body))
        else:
            log.info(
                'Page doesn\'t look like it has valid content, skipping. '
                'page=%s',
                page,
            )
        return {
            'path': page,
            'title': title,
            'sections': sections,
            'domain_data': {},
        }

    def parse_from_index_file(self, page):
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
                'Unhandled exception during search processing file: %s',
                page,
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
            log.info('Unable to read file: %s', json_path)
            raise

        data = json.loads(file_contents)
        page_data = {}

        for section in data.get('docs', []):
            parsed_path = urlparse(section.get('location', ''))
            fragment = parsed_path.fragment
            path = parsed_path.path

            # Some old versions of mkdocs
            # index the pages as ``/page.html`` insted of ``page.html``.
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
