# -*- coding: utf-8 -*-

import codecs
import logging

from pyquery import PyQuery

log = logging.getLogger(__name__)


def recurse_while_none(element):
    if element.text is None:
        return recurse_while_none(element.getchildren()[0])
    else:
        return element.text


def parse_content_from_file(documentation_type, file_path):
    try:
        with codecs.open(file_path, encoding='utf-8', mode='r') as f:
            content = f.read()
    except IOError as e:
        log.info('(Search Index) Unable to index file: %s, error :%s' % (file_path, e))
        return ''

    content = parse_content(documentation_type, content)

    if not content:
        log.info('(Search Index) Unable to index file: %s, empty file' % (file_path))
    else:
        log.debug('(Search Index) %s length: %s' % (file_path, len(content)))
    return content


def parse_content(documentation_type, content):
    """
    Prepare the text of the html file.
    Returns the body text of a document
    """
    try:
        to_index = PyQuery(content)('div[role="main"]').text()
    except ValueError:
        return ''
    return to_index


def parse_headers_from_file(documentation_type, file_path):
    log.debug('(Search Index) Parsing headers for %s' % (file_path))
    try:
        with codecs.open(file_path, encoding='utf-8', mode='r') as f:
            content = f.read()
    except IOError as e:
        log.info('(Search Index) Unable to index file: %s, error :%s' % (file_path, e))
        return ''
    headers = parse_headers(documentation_type, content)
    if not headers:
        log.error('Unable to index file headers for: %s' % file_path)
    return headers


def parse_headers(documentation_type, content):
    headers = []
    if documentation_type == 'mkdocs':
        for element in PyQuery(content)('h2'):
            headers.append(recurse_while_none(element))
    return headers


def parse_sections_from_file(documentation_type, file_path):
    log.debug('(Search Index) Parsing sections for %s' % (file_path))
    try:
        with codecs.open(file_path, encoding='utf-8', mode='r') as f:
            content = f.read()
    except IOError as e:
        log.info('(Search Index) Unable to index file: %s, error :%s' % (file_path, e))
        return ''
    sections = parse_sections(documentation_type, content)
    if not sections:
        log.error('Unable to index file sections for: %s' % file_path)
    return sections


def parse_sections(documentation_type, content):
    sections = []
    if 'sphinx' in documentation_type:
        body = PyQuery(content)
        h1_section = body('.section > h1')
        if h1_section:
            div = h1_section.parent()
            h1_title = h1_section.text().replace(u'¶', '').strip()
            h1_id = div.attr('id')
            h1_content = ""
            next_p = body('h1').next()
            while next_p:
                if next_p[0].tag == 'div' and 'class' in next_p[0].attrib:
                    if 'section' in next_p[0].attrib['class']:
                        break
                h1_content += "\n%s\n" % next_p.html()
                next_p = next_p.next()
            if h1_content:
                sections.append({
                    'id': h1_id,
                    'title': h1_title,
                    'content': h1_content,
                })

        # Capture text inside h2's
        section_list = body('.section > h2')
        for num in range(len(section_list)):
            div = section_list.eq(num).parent()
            header = section_list.eq(num)
            title = header.text().replace(u'¶', '').strip()
            section_id = div.attr('id')
            content = div.html()
            sections.append({
                'id': section_id,
                'title': title,
                'content': content,
            })
            log.debug("(Search Index) Section [%s:%s]: %s" % (section_id, title, content))
    if 'mkdocs' in documentation_type:
        try:
            body = PyQuery(content)('div[role="main"]')
        except ValueError:
            return ''

        # H1 content
        h1 = body('h1')
        h1_id = h1.attr('id')
        h1_title = h1.text().strip()
        h1_content = ""
        next_p = body('h1').next()
        while next_p:
            if next_p[0].tag == 'h2':
                break
            h1_html = next_p.html()
            if h1_html:
                h1_content += "\n%s\n" % h1_html
            next_p = next_p.next()
        if h1_content:
            sections.append({
                'id': h1_id,
                'title': h1_title,
                'content': h1_content,
            })

        # H2 content
        section_list = body('h2')
        for num in range(len(section_list)):
            h2 = section_list.eq(num)
            h2_title = h2.text().strip()
            section_id = h2.attr('id')
            h2_content = ""
            next_p = body('h2').next()
            while next_p:
                if next_p[0].tag == 'h2':
                    break
                h2_html = next_p.html()
                if h2_html:
                    h2_content += "\n%s\n" % h2_html
                next_p = next_p.next()
            if h2_content:
                sections.append({
                    'id': section_id,
                    'title': h2_title,
                    'content': h2_content,
                })
            log.debug("(Search Index) Section [%s:%s]: %s" % (section_id, h2_title, h2_content))

    return sections
