# -*- coding: utf-8 -*-
"""Utilities related to reading and generating indexable search content."""

from __future__ import absolute_import

import os
import fnmatch
import re
import codecs
import logging
import json

from builtins import next, range
from pyquery import PyQuery


log = logging.getLogger(__name__)


def process_mkdocs_json(version, build_dir=True):
    """Given a version object, return a list of page dicts from disk content."""
    if build_dir:
        full_path = version.project.full_json_path(version.slug)
    else:
        full_path = version.project.get_production_media_path(
            type_='json', version_slug=version.slug, include_file=False)

    html_files = []
    for root, _, files in os.walk(full_path):
        for filename in fnmatch.filter(files, '*.json'):
            html_files.append(os.path.join(root, filename))
    page_list = []
    for filename in html_files:
        if not valid_mkdocs_json(file_path=filename):
            continue
        relative_path = parse_path_from_file(file_path=filename)
        html = parse_content_from_file(file_path=filename)
        headers = parse_headers_from_file(documentation_type='mkdocs', file_path=filename)
        sections = parse_sections_from_file(documentation_type='mkdocs', file_path=filename)
        try:
            title = sections[0]['title']
        except IndexError:
            title = relative_path
        page_list.append({
            'content': html,
            'path': relative_path,
            'title': title,
            'headers': headers,
            'sections': sections,
        })
    return page_list


def recurse_while_none(element):
    if element.text is None:
        return recurse_while_none(element.getchildren()[0])
    return element.text


def valid_mkdocs_json(file_path):
    try:
        with codecs.open(file_path, encoding='utf-8', mode='r') as f:
            content = f.read()
    except IOError as e:
        log.warning(
            '(Search Index) Unable to index file: %s',
            file_path,
            exc_info=True,
        )
        return None

    # TODO: wrap this in a try/except block and use ``exc_info=True`` in the
    # ``log.warning`` call
    page_json = json.loads(content)
    for to_check in ['url', 'content']:
        if to_check not in page_json:
            log.warning('(Search Index) Unable to index file: %s error: Invalid JSON', file_path)
            return None

    return True


def parse_path_from_file(file_path):
    """Retrieve path information from a json-encoded file on disk."""
    try:
        with codecs.open(file_path, encoding='utf-8', mode='r') as f:
            content = f.read()
    except IOError as e:
        log.warning(
            '(Search Index) Unable to index file: %s',
            file_path,
            exc_info=True,
        )
        return ''

    # TODO: wrap this in a try/except block
    page_json = json.loads(content)
    path = page_json['url']

    # The URLs here should be of the form "path/index". So we need to
    # convert:
    #   "path/" => "path/index"
    #   "path/index.html" => "path/index"
    #   "/path/index" => "path/index"
    path = re.sub('/$', '/index', path)
    path = re.sub('\.html$', '', path)
    path = re.sub('^/', '', path)

    return path


def parse_content_from_file(file_path):
    """Retrieve content from a json-encoded file on disk."""
    try:
        with codecs.open(file_path, encoding='utf-8', mode='r') as f:
            content = f.read()
    except IOError as e:
        log.info(
            '(Search Index) Unable to index file: %s',
            file_path,
            exc_info=True,
        )
        return ''

    # TODO: wrap this in a try/except block
    page_json = json.loads(content)
    page_content = page_json['content']
    content = parse_content(page_content)

    if not content:
        log.info('(Search Index) Unable to index file: %s, empty file', file_path)
    else:
        log.debug('(Search Index) %s length: %s', file_path, len(content))
    return content


def parse_content(content):
    """
    Prepare the text of the html file.

    Returns the body text of a document
    """
    try:
        to_index = PyQuery(content).text()
    except ValueError:
        return ''
    return to_index


def parse_headers_from_file(documentation_type, file_path):
    log.debug('(Search Index) Parsing headers for %s', file_path)
    try:
        with codecs.open(file_path, encoding='utf-8', mode='r') as f:
            content = f.read()
    except IOError as e:
        log.info(
            '(Search Index) Unable to index file: %s',
            file_path,
            exc_info=True,
        )
        return ''

    # TODO: wrap this in a try/except block
    page_json = json.loads(content)
    page_content = page_json['content']
    headers = parse_headers(documentation_type, page_content)

    if not headers:
        log.error('Unable to index file headers for: %s', file_path)
    return headers


def parse_headers(documentation_type, content):
    headers = []
    if documentation_type == 'mkdocs':
        for element in PyQuery(content)('h2'):
            headers.append(recurse_while_none(element))
    return headers


def parse_sections_from_file(documentation_type, file_path):
    log.debug('(Search Index) Parsing sections for %s', file_path)
    try:
        with codecs.open(file_path, encoding='utf-8', mode='r') as f:
            content = f.read()
    except IOError as e:
        log.info(
            '(Search Index) Unable to index file: %s',
            file_path,
            exc_info=True,
        )
        return ''

    # TODO: wrap this in a try/except block
    page_json = json.loads(content)
    page_content = page_json['content']
    sections = parse_sections(documentation_type, page_content)

    if not sections:
        log.error('Unable to index file sections for: %s', file_path)
    return sections


def parse_sphinx_sections(content):
    """Generate a list of sections from sphinx-style html."""
    body = PyQuery(content)
    h1_section = body('.section > h1')
    if h1_section:
        div = h1_section.parent()
        h1_title = h1_section.text().replace(u'¶', '').strip()
        h1_id = div.attr('id')
        h1_content = ""
        next_p = next(body('h1'))  # pylint: disable=stop-iteration-return
        while next_p:
            if next_p[0].tag == 'div' and 'class' in next_p[0].attrib:
                if 'section' in next_p[0].attrib['class']:
                    break
            h1_content += "\n%s\n" % next_p.html()
            next_p = next(next_p)  # pylint: disable=stop-iteration-return
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
        title = header.text().replace(u'¶', '').strip()
        section_id = div.attr('id')
        content = div.html()
        yield {
            'id': section_id,
            'title': title,
            'content': content,
        }


def parse_mkdocs_sections(content):
    """
    Generate a list of sections from mkdocs-style html.

    May raise a ValueError
    """
    body = PyQuery(content)

    try:
        # H1 content
        h1 = body('h1')
        h1_id = h1.attr('id')
        h1_title = h1.text().strip()
        h1_content = ""
        next_p = next(body('h1'))  # pylint: disable=stop-iteration-return
        while next_p:
            if next_p[0].tag == 'h2':
                break
            h1_html = next_p.html()
            if h1_html:
                h1_content += "\n%s\n" % h1_html
            next_p = next(next_p)  # pylint: disable=stop-iteration-return
        if h1_content:
            yield {
                'id': h1_id,
                'title': h1_title,
                'content': h1_content,
            }

        # H2 content
        section_list = body('h2')
        for num in range(len(section_list)):
            h2 = section_list.eq(num)
            h2_title = h2.text().strip()
            section_id = h2.attr('id')
            h2_content = ""
            next_p = next(body('h2'))  # pylint: disable=stop-iteration-return
            while next_p:
                if next_p[0].tag == 'h2':
                    break
                h2_html = next_p.html()
                if h2_html:
                    h2_content += "\n%s\n" % h2_html
                next_p = next(next_p)  # pylint: disable=stop-iteration-return
            if h2_content:
                yield {
                    'id': section_id,
                    'title': h2_title,
                    'content': h2_content,
                }
    # we're unsure which exceptions can be raised
    except:  # noqa
        log.exception('Failed indexing')


def parse_sections(documentation_type, content):
    """Retrieve a list of section dicts from a string of html."""
    sections = []
    if 'sphinx' in documentation_type:
        sections.extend(parse_sphinx_sections(content))
    if 'mkdocs' in documentation_type:
        try:
            sections.extend(parse_mkdocs_sections(content))
        except ValueError:
            return ''

    return sections
