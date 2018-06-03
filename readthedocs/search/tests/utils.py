from readthedocs.search.tests.dummy_data import DUMMY_PAGE_JSON


def get_search_query(project_slug, page_num=0, data_type='title'):
    all_pages = DUMMY_PAGE_JSON[project_slug]
    file_data = all_pages[page_num]
    query_data = file_data[data_type]

    if data_type in ['headers']:
        # The data is in list. slice in order to get the text
        query_data = query_data[0]

    query = query_data.split()[0]
    return query
