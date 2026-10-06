import random

from django.core.management import call_command

from readthedocs.projects.models import HTMLFile
from readthedocs.search.documents import PageDocument


SECTION_FIELDS = ["section.title", "section.content"]
DATA_TYPES_VALUES = ["title"] + SECTION_FIELDS


def get_search_query_from_project_file(
    project_slug, page_num=0, field="title", type=None
):
    """
    Return search query from the project's page file.

    Query is generated from the value of `data_type`
    """

    html_file = HTMLFile.objects.filter(project__slug=project_slug).order_by("id")[
        page_num
    ]

    file_data = html_file.processed_json
    internal_type = {
        "section": "sections",
        "title": "title",
    }
    query_data = file_data[internal_type[type or field]]

    if not type and field == "title":
        # uses first word of page title as query
        query = query_data.split()[0]

    elif type == "section" and field == "title":
        # generates query from section title
        query_data = query_data[0]["title"].split()
        start = 0
        end = random.randint(1, len(query_data))
        query = query_data[start:end]
        query = " ".join(query)

    elif type == "section" and field == "content":
        # generates query from section content
        query_data = query_data[0]["content"].split()
        start = random.randint(0, 6)

        # 5 words to generate query to make sure that
        # query does not only contains 'is', 'and', 'the'
        # and other stop words
        end = start + 5

        query = query_data[start:end]
        query = " ".join(query)

    return query


class SearchIndexTestMixin:
    """
    Create the search indexes once per test class, and clear their documents after each test.

    Creating and deleting indexes are cluster state changes,
    doing them around every test can stall ES for longer than the client's timeout on CI.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("search_index", "--delete", "-f")
        call_command("search_index", "--create")

    @classmethod
    def tearDownClass(cls):
        call_command("search_index", "--delete", "-f")
        super().tearDownClass()

    def tearDown(self):
        super().tearDown()
        PageDocument.search().query("match_all").params(refresh=True).delete()
