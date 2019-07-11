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

        # use first word of page title as query
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
        if data_type.endswith('content'):
            query_data = query_data[0]['content'].split()
            start = random.randint(0, 6)

            # 3 words to generate query to make sure that
            # query does not only contains 'is', 'and', 'the'
            # and other stop words
            end = start + 3

            query = query_data[start:end]
            query = ' '.join(query)
    
    return query
