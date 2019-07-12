"""Functions related to converting content into dict/JSON structures."""

import codecs
import json
import logging

from pyquery import PyQuery


log = logging.getLogger(__name__)


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

            h1_content += parse_content(next_p.text())
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
        content = parse_content(content)

        yield {
            'id': section_id,
            'title': title,
            'content': content,
        }


def process_file(fjson_filename):
    """Read the fjson file from disk and parse it into a structured dict."""
    try:
        with codecs.open(fjson_filename, encoding='utf-8', mode='r') as f:
            file_contents = f.read()
    except IOError:
        log.info('Unable to read file: %s', fjson_filename)
        raise
    data = json.loads(file_contents)
    sections = []
    path = ''
    title = ''

    if 'current_page_name' in data:
        path = data['current_page_name']
    else:
        log.info('Unable to index file due to no name %s', fjson_filename)

    if data.get('body'):
        body = PyQuery(data['body'])
        sections.extend(generate_sections_from_pyquery(body))
    else:
        log.info('Unable to index content for: %s', fjson_filename)

    if 'title' in data:
        title = data['title']
        if title.startswith('<'):
            title = PyQuery(data['title']).text()
    else:
        log.info('Unable to index title for: %s', fjson_filename)

    return {
        'path': path,
        'title': title,
        'sections': sections,
    }


def parse_content(content):
    """
    Removes the starting text and ¶.

    It removes the starting text from the content
    because it contains the the title of that content,
    which is redundant here.
    """
    content = content.replace('¶', '').strip()

    # removing the starting text of each
    content = content.split('\n')
    if len(content) > 1:  # there were \n
        content = content[1:]

    # converting newlines to ". "
    content = '. '.join([text.strip() for text in content])
    return content
