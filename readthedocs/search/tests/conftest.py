import random
import string
from random import shuffle

import pytest
from django.core.management import call_command
from django_dynamic_fixture import G

from readthedocs.projects.models import Project
from readthedocs.search.indexes import Index, ProjectIndex, PageIndex, SectionIndex
from .dummy_data import DUMMY_PAGE_JSON, ALL_PROJECTS


@pytest.fixture(autouse=True)
def mock_elastic_index(mocker):
    index_name = ''.join([random.choice(string.ascii_letters) for _ in range(5)])
    mocker.patch.object(Index, '_index', index_name.lower())


@pytest.fixture()
def es_index():
    call_command('search_index', '--delete', '-f')
    call_command('search_index', '--create')

    yield
    call_command('search_index', '--delete', '-f')


@pytest.fixture
def all_projects(es_index):
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
