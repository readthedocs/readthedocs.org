# -*- coding: utf-8 -*-

import random

from readthedocs.projects.models import HTMLFile


def get_search_query_from_project_file(project_slug, page_num=0, data_type='title'):
    """
    Return search query from the project's page file.

    Query is generated from the value of `data_type`
    """

    html_file = HTMLFile.objects.filter(project__slug=project_slug).order_by('id')[page_num]

    file_data = html_file.processed_json
    query_data = file_data[data_type.split('.')[0]]

    if data_type == 'title':

        # uses first word of page title as query
        query = query_data.split()[0]

    elif data_type.startswith('sections'):

        # generates query from section title
        if data_type.endswith('title'):
            query_data = query_data[0]['title'].split()
            start = 0
            end = random.randint(1, len(query_data))
            query = query_data[start:end]
            query = ' '.join(query)

        # generates query from section content
        elif data_type.endswith('content'):
            query_data = query_data[0]['content'].split()
            start = random.randint(0, 6)

            # 3 words to generate query to make sure that
            # query does not only contains 'is', 'and', 'the'
            # and other stop words
            end = start + 3

            query = query_data[start:end]
            query = ' '.join(query)

    elif data_type.startswith('domains'):

        # uses first word of domains.type_display as query
        if data_type.endswith('type_display'):
            query = query_data[0]['type_display'].split()[0]

        # generates query from domains.name
        if data_type.endswith('name'):
            # test data contains domains.name
            # some of which contains '.' and some '/'
            # and others are plain words.
            # Splitting with '.' and '/' is done
            # to ensure that the query contains proper words
            if '.' in query_data[0]['name']:
                query_data = query_data[0]['name'].split('.')
                start = 0
                end = random.randint(1, len(query_data))
                query = '.'.join(query_data[start:end])

            elif '/' in query_data[0]['name']:
                query_data = query_data[0]['name'].split('/')
                start = 0
                end = random.randint(1, len(query_data))
                query = '/'.join(query_data[start:end])
            else:
                query = query_data[0]['name'].split()[0]

    return query
