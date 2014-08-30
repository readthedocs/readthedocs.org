# -*- coding: utf-8 -*-

import codecs
import fnmatch
import json
import os

from pyquery import PyQuery

import logging
log = logging.getLogger(__name__)


def process_all_json_files(version, build_dir=True):
    """
    Return a list of pages to index
    """
    if build_dir:
        full_path = version.project.full_json_path(version.slug)
    else:
        full_path = version.project.get_production_media_path(type='json', version_slug=version.slug, include_file=False)
    html_files = []
    for root, dirs, files in os.walk(full_path):
        for filename in fnmatch.filter(files, '*.fjson'):
            if filename in ['search.fjson', 'genindex.fjson', 'py-modindex.fjson']:
                continue
            html_files.append(os.path.join(root, filename))
    page_list = []
    for filename in html_files:
        result = process_file(filename)
        if result:
            page_list.append(result)
    return page_list


def process_file(filename):
    try:
        with codecs.open(filename, encoding='utf-8', mode='r') as f:
            file_contents = f.read()
    except IOError as e:
        log.info('Unable to index file: %s, error :%s' % (filename, e))
        return
    data = json.loads(file_contents)
    headers = []
    sections = []
    content = ''
    title = ''
    body_content = ''
    if 'current_page_name' in data:
        path = data['current_page_name']
    else:
        log.error('Unable to index file due to no name %s' % filename)
        return None
    if 'toc' in data:
        for element in PyQuery(data['toc'])('a'):
            headers.append(recurse_while_none(element))
        if None in headers:
            log.error('Unable to index file headers for: %s' % filename)
    if 'body' in data and len(data['body']):
        body = PyQuery(data['body'])
        body_content = body.text().replace(u'¶', '')
        # Capture text inside h1 before the first h2
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

    else:
        log.error('Unable to index content for: %s' % filename)
    if 'title' in data:
        title = data['title']
        if title.startswith('<'):
            title = PyQuery(data['title']).text()
    else:
        log.error('Unable to index title for: %s' % filename)

    return {'headers': headers, 'content': body_content, 'path': path,
            'title': title, 'sections': sections}

def recurse_while_none(element):
    if element.text is None:
        return recurse_while_none(element.getchildren()[0])
    else:
        return element.text
