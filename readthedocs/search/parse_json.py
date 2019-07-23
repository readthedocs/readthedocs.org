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
    domain_data = {}

    if 'current_page_name' in data:
        path = data['current_page_name']
    else:
        log.info('Unable to index file due to no name %s', fjson_filename)

    if data.get('body'):
        body = PyQuery(data['body'])
        sections.extend(generate_sections_from_pyquery(body))
        domain_data = generate_domains_data_from_pyquery(body)
    else:
        log.info('Unable to index content for: %s', fjson_filename)

    if 'title' in data:
        title = data['title']
        title = PyQuery(data['title']).text().replace('¶', '').strip()
    else:
        log.info('Unable to index title for: %s', fjson_filename)

    return {
        'path': path,
        'title': title,
        'sections': sections,
        'domain_data': domain_data,
    }


def parse_content(content):
    """
    Removes the starting text and ¶.

    It removes the starting text from the content
    because it contains the title of that content,
    which is redundant here.
    """
    content = content.replace('¶', '').strip()

    # removing the starting text of each
    content = content.split('\n')
    if len(content) > 1:  # there were \n
        content = content[1:]

    # converting newlines to ". "
    content = '. '.join([text.strip().rstrip('.') for text in content])
    return content


def generate_domains_data_from_pyquery(body):

    dl_tags = body('dl')
    domain_data = {}

    for dl_tag in dl_tags:

        dt = dl_tag.findall('dt')  
        dd = dl_tag.findall('dd')

        # len(dt) should be equal to len(dd)
        # becuase these tags go together.
        for title, desc in zip(dt, dd):
            id_ = title.attrib.get('id')
            if id_:
                # clone the PyQuery objects so that
                # the original one remains undisturbed
                desc_contents = PyQuery(desc).clone()

                # remove the 'dl', 'dt' and 'dd' tags from it
                # because all the 'dd' and 'dt' tags are inside 'dl'
                # and all 'dl' tags are already captured.
                desc_contents.remove('dl')
                desc_contents.remove('dt')
                desc_contents.remove('dd')

                docstrings = desc_contents.text().replace('¶', '').strip()
                docstrings = '. '.join(
                    [
                        text.strip().rstrip('.') for text in docstrings.split('\n')
                    ]
                )
                domain_data[id_] = docstrings

    return domain_data
