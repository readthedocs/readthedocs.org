"""Functions related to converting content into dict/JSON structures."""

import logging
from urllib.parse import urlparse

import orjson as json
from django.conf import settings
from django.core.files.storage import get_storage_class
from selectolax.parser import HTMLParser

log = logging.getLogger(__name__)


def generate_page_sections(page_title, body, fjson_storage_path):
    """
    Generate section dicts for each section for sphinx.

    In Sphinx sub-sections are nested, so they are children of the outer section,
    and sections with the same level are neighbors.
    We index the content under a section till before the next one.

    We can have pages that have content before the first title or that don't have a title,
    we index that content first under the title of the original page (`page_title`).

    Contents that are likely to be a sphinx domain are deleted,
    since we already index those in another step.
    """

    # Removing all <dl> tags to prevent duplicate indexing with Sphinx Domains.
    nodes_to_be_removed = []
    try:
        # remove all <dl> tags which contains <dt> tags having 'id' attribute
        dt_tags = body.css('dt[id]')
        for tag in dt_tags:
            parent = tag.parent
            if parent.tag == 'dl':
                nodes_to_be_removed.append(parent)
    except Exception:
        log.exception('Error removing <dl> tags from file: %s', fjson_storage_path)

    # remove `Table of Contents` elements
    try:
        nodes_to_be_removed += body.css('.toctree-wrapper') + body.css('.contents.local.topic')
    except Exception:
        log.exception('Error removing "Table of Content" tags from file: %s', fjson_storage_path)

    # removing all nodes in list
    for node in nodes_to_be_removed:
        node.decompose()

    # Index content for pages that don't start with a title.
    content, blocks = _get_content_from_tag(body.body.child)
    if content:
        yield {
            'id': '',
            'title': page_title,
            'content': content,
            'blocks': blocks,
        }

    # Index content from h1 to h6 headers.
    for head_level in range(1, 7):
        tags = body.css(f'.section > h{head_level}')
        for tag in tags:
            title = tag.text().replace('¶', '').strip()

            div = tag.parent
            section_id = div.attributes.get('id', '')
            content, blocks = _get_content_from_tag(tag.next)

            yield {
                'id': section_id,
                'title': title,
                'content': content,
                'blocks': blocks,
            }


def _get_content_from_tag(tag):
    """Gets the content and blocks from `tag` till before a new section."""
    contents = []
    blocks = []

    next_tag = tag
    char_count = 0
    while next_tag and not _is_section(next_tag):
        if _is_code_section(next_tag):
            content = _parse_code_section(next_tag)
            if content:
                content = '\n' + content + '\n'
                start = char_count + 1
                end = start + len(content) - 1
                blocks.append(
                    {
                        'start': start,
                        'end': end,
                        'type': 'codeblock',
                        'context': '',
                    }
                )
        else:
            content = parse_content(next_tag.text())

        if content:
            char_count += len(content) + 1
            contents.append(content)

        next_tag = next_tag.next
    return ' '.join(contents), blocks


def _is_code_section(tag):
    """
    Check if `tag` is a code section.

    Sphinx codeblocks have a class named ``highlight-{language}``.
    """
    for c in tag.attributes.get('class', '').split():
        if c.startswith('highlight'):
            return True
    return False


def _is_section(tag):
    """Check if `tag` is a sphinx section (linkeable header)."""
    return (
        tag.tag == 'div' and
        'section' in tag.attributes.get('class', '').split()
    )


def _parse_code_section(tag):
    """
    Parse a code section to fetch relevant content only.

    Sphinx has ``pre`` tags within a div with a ``highlight`` class.
    Other ``pre`` tags are used for line numbers (we don't index those).
    """
    contents = []
    for node in tag.css('pre'):
        parent = node.parent
        is_code_block = (
            parent and
            parent.tag == 'div' and
            parent.attributes.get('class') == 'highlight'
        )
        if is_code_block:
            content = node.text().strip('\n').rstrip()
            contents.append(content)
    return '\n'.join(contents)


def process_file(fjson_storage_path):
    """Read the fjson file from disk and parse it into a structured dict."""
    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()

    log.debug('Processing JSON file for indexing: %s', fjson_storage_path)

    try:
        with storage.open(fjson_storage_path, mode='r') as f:
            file_contents = f.read()
    except IOError:
        log.info('Unable to read file: %s', fjson_storage_path)
        raise

    data = json.loads(file_contents)
    sections = []
    path = ''
    title = ''
    domain_data = {}

    if 'current_page_name' in data:
        path = data['current_page_name']
    else:
        log.info('Unable to index file due to no name %s', fjson_storage_path)

    if 'title' in data:
        title = data['title']
        title = HTMLParser(title).text().replace('¶', '').strip()
    else:
        log.info('Unable to index title for: %s', fjson_storage_path)

    if data.get('body'):
        body = HTMLParser(data['body'])
        body_copy = HTMLParser(data['body'])
        sections = generate_page_sections(
            page_title=title,
            body=body,
            fjson_storage_path=fjson_storage_path,
        )

        # pass a copy of `body` so that the removed
        # nodes in the original don't reflect here.
        domain_data = generate_domains_data(body_copy, fjson_storage_path)
    else:
        log.info('Unable to index content for: %s', fjson_storage_path)

    return {
        'path': path,
        'title': title,
        'sections': list(sections),
        'domain_data': domain_data,
    }


def generate_domains_data(body, fjson_storage_path):
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
                    docstrings = _get_text_for_domain_data(desc)
                    domain_data[id_] = docstrings
            except Exception:
                log.exception('Error parsing docstrings for domains in file %s', fjson_storage_path)

    return domain_data


def _get_text_for_domain_data(desc):
    """Returns the text from the dom node."""

    # remove the 'dl', 'dt' and 'dd' tags from it
    # because all the 'dd' and 'dt' tags are inside 'dl'
    # and all 'dl' tags are already captured.
    nodes_to_be_removed = desc.css('dl') + desc.css('dt') + desc.css('dd')
    for node in nodes_to_be_removed:
        node.decompose()

    # remove multiple spaces, new line characters and '¶' symbol.
    docstrings = parse_content(desc.text())
    return docstrings


def parse_content(content, remove_first_line=False):
    """Removes new line characters and ¶."""
    content = content.replace('¶', '').strip()
    content = content.split('\n')

    # removing the starting text of each
    if remove_first_line and len(content) > 1:
        content = content[1:]

    # Convert all new lines to " "
    content = (text.strip() for text in content)
    content = ' '.join(text for text in content if text)
    return content


def process_mkdocs_index_file(json_storage_path, page):
    """Reads the json index file and parses it into a structured dict."""
    log.debug('Processing JSON index file: %s', json_storage_path)

    storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
    try:
        with storage.open(json_storage_path, mode='r') as f:
            file_contents = f.read()
    except IOError:
        log.info('Unable to read file: %s', json_storage_path)
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

        title = HTMLParser(section.get('title')).text()
        content = parse_content(
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
            'blocks': [],
        })

    return page_data
