"""Functions related to converting content into dict/JSON structures."""

import json
import logging

from django.conf import settings
from django.core.files.storage import get_storage_class

from pyquery import PyQuery


log = logging.getLogger(__name__)


def process_headers(data, filename):
    """Read headers from toc data."""
    headers = []
    if data.get('toc', False):
        for element in PyQuery(data['toc'])('a'):
            headers.append(recurse_while_none(element))
        if None in headers:
            log.info('Unable to index file headers for: %s', filename)
    return headers


def generate_sections_from_pyquery(body):
    """Given a pyquery object, generate section dicts for each section."""
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
            h1_content += '\n%s\n' % next_p.html()
            next_p = next_p.next()
        if h1_content:
            yield {
                'id': h1_id,
                'title': h1_title,
                'content': h1_content,
            }

    # Capture text inside h2's
    section_list = body('.section > h2')
    for num in range(len(section_list)):
        div = section_list.eq(num).parent()
        header = section_list.eq(num)
        title = header.text().replace('¶', '').strip()
        section_id = div.attr('id')
        content = div.html()
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
    body_content = ''

    if 'current_page_name' in data:
        path = data['current_page_name']
    else:
        log.info('Unable to index file due to no name %s', fjson_storage_path)

    if data.get('body'):
        body = PyQuery(data['body'])
        body_content = body.text().replace('¶', '')
        sections.extend(generate_sections_from_pyquery(body))
    else:
        log.info('Unable to index content for: %s', fjson_storage_path)

    if 'title' in data:
        title = data['title']
        if title.startswith('<'):
            title = PyQuery(data['title']).text()
    else:
        log.info('Unable to index title for: %s', fjson_storage_path)

    return {
        'headers': process_headers(data, fjson_storage_path),
        'content': body_content,
        'path': path,
        'title': title,
        'sections': sections,
    }


def recurse_while_none(element):
    """
    Traverse the ``element`` until a non-None text is found.

    :param element: element to traverse until get a non-None text.
    :type element: pyquery.PyQuery

    :returns: the first non-None value found
    :rtype: str
    """
    if element.text is None:
        return recurse_while_none(element.getchildren()[0])
    return element.text
