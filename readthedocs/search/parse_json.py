"""Functions related to converting content into dict/JSON structures."""

import codecs
import json
import logging

from pyquery import PyQuery


log = logging.getLogger(__name__)


def generate_sections_from_pyquery(body):
    """Given a pyquery object, generate section dicts for each section."""

    # Removing all <dl>, <dd> and <dt> tags
    # to prevent duplicate indexing with Sphinx Domains.
    body('dl').remove()
    body('dd').remove()
    body('dt').remove()

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

    if data.get('body'):
        body = PyQuery(data['body'])
        sections.extend(generate_sections_from_pyquery(body.clone()))
        domain_data = generate_domains_data_from_pyquery(body.clone(), fjson_filename)
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
