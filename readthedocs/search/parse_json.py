# -*- coding: utf-8 -*-

import codecs
import fnmatch
import json
import os

from pyquery import PyQuery

import logging
log = logging.getLogger(__name__)


def process_all_json_files(version):
    full_path = version.project.full_json_path(version.slug)
    html_files = []
    for root, dirs, files in os.walk(full_path):
        for filename in fnmatch.filter(files, '*.fjson'):
            if filename in ['genindex.fjson', 'py-modindex.fjson']:
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
    content = ''
    title = ''
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
    if 'body' in data:
        content = PyQuery(data['body']).text().replace(u'¶', '')
    else:
        log.error('Unable to index content for: %s' % filename)
    if 'title' in data:
        title = data['title']
    else:
        log.error('Unable to index title for: %s' % filename)

    return {'headers': headers, 'content': content, 'path': path,
            'title': title}

def recurse_while_none(element):
    if element.text is None:
        return recurse_while_none(element.getchildren()[0])
    else:
        return element.text
