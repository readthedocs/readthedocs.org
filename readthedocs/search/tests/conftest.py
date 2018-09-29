import json
import os
from random import shuffle

import pytest
from django.core.management import call_command
from django_dynamic_fixture import G

from readthedocs.projects.models import Project, HTMLFile
from .dummy_data import ALL_PROJECTS, PROJECT_DATA_FILES


@pytest.fixture()
def es_index():
    call_command('search_index', '--delete', '-f')
    call_command('search_index', '--create')

    yield
    call_command('search_index', '--delete', '-f')


@pytest.fixture(autouse=True)
def all_projects(es_index, mock_processed_json, db, settings):
    settings.ELASTICSEARCH_DSL_AUTOSYNC = True
    projects_list = []
    for project_slug in ALL_PROJECTS:
        project = G(Project, slug=project_slug, name=project_slug)

        for file_basename in PROJECT_DATA_FILES[project.slug]:
            # file_basename in config are without extension so add html extension
            file_name = file_basename + '.html'
            version = project.versions.all()[0]
            f = G(HTMLFile, project=project, version=version, name=file_name)
            f.save()

        projects_list.append(project)

    shuffle(projects_list)
    return projects_list


@pytest.fixture
def project(all_projects):
    # Return a single project
    return all_projects[0]


def get_dummy_processed_json(instance):
    project_slug = instance.project.slug
    basename = os.path.splitext(instance.name)[0]
    file_name = basename + '.json'
    current_path = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(current_path, "data", project_slug, file_name)

    if os.path.exists(file_path):
        with open(file_path) as f:
            return json.load(f)


@pytest.fixture(autouse=True)
def mock_processed_json(mocker):
    mocked_function = mocker.patch.object(HTMLFile, 'get_processed_json', autospec=True)
    mocked_function.side_effect = get_dummy_processed_json
