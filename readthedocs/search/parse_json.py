# -*- coding: utf-8 -*-

"""Functions related to converting content into dict/JSON structures."""

import codecs
import json
import logging

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


def process_file(filename):
    """Read a file from disk and parse it into a structured dict."""
    try:
        with codecs.open(filename, encoding='utf-8', mode='r') as f:
            file_contents = f.read()
    except IOError:
        log.info('Unable to read file: %s', filename)
        return None
    data = json.loads(file_contents)
    sections = []
    title = ''
    body_content = ''
    if 'current_page_name' in data:
        path = data['current_page_name']
    else:
        log.info('Unable to index file due to no name %s', filename)
        return None
    if 'body' in data and data['body']:
        body = PyQuery(data['body'])
        body_content = body.text().replace('¶', '')
        sections.extend(generate_sections_from_pyquery(body))
    else:
        log.info('Unable to index content for: %s', filename)
    if 'title' in data:
        title = data['title']
        if title.startswith('<'):
            title = PyQuery(data['title']).text()
    else:
        log.info('Unable to index title for: %s', filename)

    return {
        'headers': process_headers(data, filename),
        'content': body_content,
        'path': path,
        'title': title,
        'sections': sections,
    }


def recurse_while_none(element):
    if element.text is None:
        return recurse_while_none(element.getchildren()[0])
    return element.text
