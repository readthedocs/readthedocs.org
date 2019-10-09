"""Functions related to converting content into dict/JSON structures."""

import logging
import orjson as json

from django.conf import settings
from django.core.files.storage import get_storage_class

from selectolax.parser import HTMLParser


log = logging.getLogger(__name__)


def generate_page_sections(body, fjson_storage_path):
    """Generate section dicts for each section."""

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

    # Capture text inside h1 before the first h2
    h1_section = body.css('.section > h1')
    if h1_section:
        h1_section = h1_section[0]
        div = h1_section.parent
        h1_title = h1_section.text().replace('¶', '').strip()
        h1_id = div.attributes.get('id', '')
        h1_content = ''
        next_p = body.css_first('h1').next
        while next_p:
            if next_p.tag == 'div' and 'class' in next_p.attributes:
                if 'section' in next_p.attributes['class']:
                    break

            text = parse_content(next_p.text(), remove_first_line=False)

            if h1_content:
                if text:
                    h1_content = f'{h1_content} {text}'
            else:
                h1_content = text

            next_p = next_p.next

        if h1_content:
            yield {
                'id': h1_id,
                'title': h1_title,
                'content': h1_content,
            }

    # Capture text inside h2's
    section_list = body.css('.section > h2')
    for tag in section_list:
        div = tag.parent
        title = tag.text().replace('¶', '').strip()
        section_id = div.attributes.get('id', '')

        content = div.text()
        content = parse_content(content, remove_first_line=True)

        if content:
            yield {
                'id': section_id,
                'title': title,
                'content': content,
            }


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

    if data.get('body'):
        body = HTMLParser(data['body'])
        body_copy = HTMLParser(data['body'])
        sections = generate_page_sections(body, fjson_storage_path)

        # pass a copy of `body` so that the removed
        # nodes in the original don't reflect here.
        domain_data = generate_domains_data(body_copy, fjson_storage_path)
    else:
        log.info('Unable to index content for: %s', fjson_storage_path)

    if 'title' in data:
        title = data['title']
        title = HTMLParser(title).text().replace('¶', '').strip()
    else:
        log.info('Unable to index title for: %s', fjson_storage_path)

    return {
        'path': path,
        'title': title,
        'sections': tuple(sections),
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

    # removing the starting text of each
    content = content.split('\n')
    if remove_first_line and len(content) > 1:
        content = content[1:]

    # converting newlines to ". "
    content = ' '.join([text.strip() for text in content if text])
    return content
