# -*- coding: utf-8 -*-

import random

from readthedocs.projects.models import HTMLFile


SECTION_FIELDS = [ 'sections.title', 'sections.content' ]
DOMAIN_FIELDS = [ 'domains.name', 'domains.docstrings' ]
DATA_TYPES_VALUES = ['title'] + SECTION_FIELDS + DOMAIN_FIELDS


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

    elif data_type == 'sections.title':

        # generates query from section title
        query_data = query_data[0]['title'].split()
        start = 0
        end = random.randint(1, len(query_data))
        query = query_data[start:end]
        query = ' '.join(query)

    elif data_type == 'sections.content':

        # generates query from section content
        query_data = query_data[0]['content'].split()
        start = random.randint(0, 6)

        # 5 words to generate query to make sure that
        # query does not only contains 'is', 'and', 'the'
        # and other stop words
        end = start + 5

        query = query_data[start:end]
        query = ' '.join(query)

    elif data_type == 'domains.name':
        # test data contains domains.name
        # some of which contains '.' and some '/'
        # and others are plain words.
        # Splitting with '.' and '/' is done
        # to ensure that the query contains proper words

        # generates query from domains.name
        if '.' in query_data[0]['name']:
            query_data = query_data[0]['name'].split('.')
            start = 0
            end = random.randint(1, len(query_data))
            query = '.'.join(query_data[start:end])

        elif '/' in query_data[0]['name']:
            query_data = query_data[0]['name']

            # this is done to remove empty query
            query_data = [word for word in query_data.split('/') if word]
            start = 0
            end = random.randint(1, len(query_data))
            query = '/'.join(query_data[start:end])
        else:
            query = query_data[0]['name'].split()[0]

    elif data_type == 'domains.docstrings':

        # generates query from domain docstrings
        anchor = query_data[0]['anchor']
        docstrings = file_data['domain_data'][anchor]
        query_data = docstrings.split()
        start = random.randint(0, 1)

        # 5 words to generate query to make sure that
        # query does not only contains 'is', 'and', 'the'
        # and other stop words
        end = start + 5

        query = query_data[start:end]
        query = ' '.join(query)

    return query
