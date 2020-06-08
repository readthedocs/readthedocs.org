import json
import os
from random import shuffle

import pytest
from django.core.management import call_command
from django_dynamic_fixture import get

from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search.documents import PageDocument
from readthedocs.sphinx_domains.models import SphinxDomain

from .dummy_data import ALL_PROJECTS, PROJECT_DATA_FILES


@pytest.fixture
def es_index():
    call_command('search_index', '--delete', '-f')
    call_command('search_index', '--create')

    yield
    call_command('search_index', '--delete', '-f')


@pytest.fixture
def all_projects(es_index, mock_processed_json, db, settings):
    settings.ELASTICSEARCH_DSL_AUTOSYNC = True
    projects_list = []
    for project_slug in ALL_PROJECTS:
        project = get(
            Project,
            slug=project_slug,
            name=project_slug,
            main_language_project=None,
            privacy_level=PUBLIC,
        )
        project.versions.update(privacy_level=PUBLIC)

        for file_basename in PROJECT_DATA_FILES[project.slug]:
            # file_basename in config are without extension so add html extension
            file_name = file_basename + '.html'
            version = project.versions.all()[0]
            html_file = get(
                HTMLFile,
                project=project,
                version=version,
                name=file_name,
                path=file_name,
            )

            # creating sphinx domain test objects
            file_path = get_json_file_path(project.slug, file_basename)
            if os.path.exists(file_path):
                with open (file_path) as f:
                    data = json.load(f)
                    domains = data['domains']

                    for domain_data in domains:
                        domain_role_name = domain_data.pop('role_name')
                        domain, type_ = domain_role_name.split(':')

                        get(
                            SphinxDomain,
                            project=project,
                            version=version,
                            html_file=html_file,
                            domain=domain,
                            type=type_,
                            **domain_data
                        )

            PageDocument().update(html_file)

        projects_list.append(project)

    shuffle(projects_list)
    return projects_list


@pytest.fixture
def project(all_projects):
    # Return a single project
    return all_projects[0]


def get_json_file_path(project_slug, basename):
    current_path = os.path.abspath(os.path.dirname(__file__))
    file_name = f'{basename}.json'
    file_path = os.path.join(current_path, 'data', project_slug, file_name)
    return file_path


def get_dummy_processed_json(instance):
    project_slug = instance.project.slug
    basename = os.path.splitext(instance.name)[0]
    file_path = get_json_file_path(project_slug, basename)

    if os.path.exists(file_path):
        with open(file_path) as f:
            return json.load(f)


@pytest.fixture
def mock_processed_json(mocker):
    mocked_function = mocker.patch.object(HTMLFile, 'get_processed_json', autospec=True)
    mocked_function.side_effect = get_dummy_processed_json
