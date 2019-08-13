"""Functions related to converting content into dict/JSON structures."""

import json
import logging

from django.conf import settings
from django.core.files.storage import get_storage_class

from pyquery import PyQuery


log = logging.getLogger(__name__)


def generate_sections_from_pyquery(body, fjson_filename):
    """Given a pyquery object, generate section dicts for each section."""

    # Removing all <dl> tags to prevent duplicate indexing with Sphinx Domains.
    try:
        # remove all <dl> tags which contains <dt> tags having 'id' attribute
        dt_tags = body('dt[id]')
        dt_tags.parents('dl').remove()
    except Exception:
        log.exception('Error removing <dl> tags from file: %s', fjson_filename)

    # remove toctree elements
    try:
        body('.toctree-wrapper').remove()
    except Exception:
        log.exception('Error removing toctree elements from file: %s', fjson_filename)

    # Capture text inside h1 before the first h2
    h1_section = body('.section > h1')
    if h1_section:
        div = h1_section.parent()
        h1_title = h1_section.text().replace('¶', '').strip()
        h1_id = div.attr('id')
        h1_content = ''
        next_p = body('h1').next()
        while next_p:
            if next_p[0].tag == 'div' and 'class' in next_p[0].attrib:
                if 'section' in next_p[0].attrib['class']:
                    break

            text = parse_content(next_p.text(), remove_first_line=True)
            if h1_content:
                h1_content = f'{h1_content.rstrip(".")}. {text}'
            else:
                h1_content = text

            next_p = next_p.next()
        if h1_content:
            yield {
                'id': h1_id,
                'title': h1_title,
                'content': h1_content.replace('\n', '. '),
            }

    # Capture text inside h2's
    section_list = body('.section > h2')
    for num in range(len(section_list)):
        div = section_list.eq(num).parent()
        header = section_list.eq(num)
        title = header.text().replace('¶', '').strip()
        section_id = div.attr('id')

        content = div.text()
        content = parse_content(content, remove_first_line=True)

        yield {
            'id': section_id,
            'title': title,
            'content': content,
        }


def process_file(fjson_storage_path):
    """Read the fjson file from disk and parse it into a structured dict."""
    if not settings.RTD_BUILD_MEDIA_STORAGE:
        log.warning('RTD_BUILD_MEDIA_STORAGE is missing - Not updating intersphinx data')
        raise RuntimeError('RTD_BUILD_MEDIA_STORAGE is missing - Not updating intersphinx data')

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
        body = PyQuery(data['body'])
        sections.extend(generate_sections_from_pyquery(body.clone(), fjson_filename))
        domain_data = generate_domains_data_from_pyquery(body.clone(), fjson_filename)
    else:
        log.info('Unable to index content for: %s', fjson_storage_path)

    if 'title' in data:
        title = data['title']
        title = PyQuery(data['title']).text().replace('¶', '').strip()
    else:
        log.info('Unable to index title for: %s', fjson_storage_path)

    return {
        'path': path,
        'title': title,
        'sections': sections,
        'domain_data': domain_data,
    }


def parse_content(content, remove_first_line=False):
    """Removes new line characters and ¶."""
    content = content.replace('¶', '').strip()

    # removing the starting text of each
    content = content.split('\n')
    if remove_first_line and len(content) > 1:
        content = content[1:]

    # converting newlines to ". "
    content = '. '.join([text.strip().rstrip('.') for text in content])
    return content


def _get_text_for_domain_data(desc_contents):
    """Returns the text from the PyQuery object ``desc_contents``."""
    # remove the 'dl', 'dt' and 'dd' tags from it
    # because all the 'dd' and 'dt' tags are inside 'dl'
    # and all 'dl' tags are already captured.
    desc_contents.remove('dl')
    desc_contents.remove('dt')
    desc_contents.remove('dd')

    # remove multiple spaces, new line characters and '¶' symbol.
    docstrings = parse_content(desc_contents.text())
    return docstrings


def generate_domains_data_from_pyquery(body, fjson_filename):
    """
    Given a pyquery object, generate sphinx domain objects' docstrings.

    Returns a dict with the generated data.
    The returned dict is in the following form::

        {
            "domain-id-1": "docstrings for the domain-id-1",
            "domain-id-2": "docstrings for the domain-id-2",
        }
    """

    domain_data = {}
    dl_tags = body('dl')

    for dl_tag in dl_tags:

        dt = dl_tag.findall('dt')
        dd = dl_tag.findall('dd')

        # len(dt) should be equal to len(dd)
        # because these tags go together.
        for title, desc in zip(dt, dd):
            try:
                id_ = title.attrib.get('id')
                if id_:
                    # clone the PyQuery objects so that
                    # the original one remains undisturbed
                    docstrings = _get_text_for_domain_data(PyQuery(desc).clone())
                    domain_data[id_] = docstrings
            except Exception:
                log.exception('Error parsing docstrings for domains in file %s', fjson_filename)

    return domain_data
