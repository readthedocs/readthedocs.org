# -*- coding: utf-8 -*-
from readthedocs.projects.models import HTMLFile


def get_search_query_from_project_file(project_slug, page_num=0, data_type='title'):
    """
    Return search query from the project's page file.

    Query is generated from the value of `data_type`
    """

    html_file = HTMLFile.objects.filter(project__slug=project_slug).order_by('id')[page_num]

    file_data = html_file.processed_json
    query_data = file_data[data_type]

    if data_type in ['headers']:
        # The data is in list. slice in order to get the text
        query_data = query_data[0]

    query = query_data.split()[0]
    return query
