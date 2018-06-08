import random
import string
from random import shuffle

import pytest
from django_dynamic_fixture import G

from readthedocs.projects.models import Project
from readthedocs.search.indexes import Index, ProjectIndex, PageIndex, SectionIndex
from .dummy_data import DUMMY_PAGE_JSON, ALL_PROJECTS


@pytest.fixture(autouse=True)
def mock_elastic_index(mocker):
    index_name = ''.join([random.choice(string.ascii_letters) for _ in range(5)])
    mocker.patch.object(Index, '_index', index_name.lower())


@pytest.fixture(autouse=True)
def es_index(mock_elastic_index):
    # Create the index.
    index = Index()
    index_name = index.timestamped_index()
    index.create_index(index_name)
    index.update_aliases(index_name)
    # Update mapping
    proj = ProjectIndex()
    proj.put_mapping()
    page = PageIndex()
    page.put_mapping()
    sec = SectionIndex()
    sec.put_mapping()

    yield index
    index.delete_index(index_name=index_name)


@pytest.fixture
def all_projects():
    projects = [G(Project, slug=project_slug, name=project_slug) for project_slug in ALL_PROJECTS]
    shuffle(projects)
    return projects


@pytest.fixture
def project(all_projects):
    # Return a single project
    return all_projects[0]


def get_dummy_page_json(version, *args, **kwargs):
    dummy_page_json = DUMMY_PAGE_JSON
    project_name = version.project.name
    return dummy_page_json.get(project_name)


@pytest.fixture(autouse=True)
def mock_parse_json(mocker):

    # patch the function from `projects.tasks` because it has been point to there
    # http://www.voidspace.org.uk/python/mock/patch.html#where-to-patch
    mocked_function = mocker.patch('readthedocs.projects.tasks.process_all_json_files')
    mocked_function.side_effect = get_dummy_page_json
