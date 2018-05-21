import json
import pytest
from django_dynamic_fixture import G
from faker import Faker

from readthedocs.projects.models import Project
from readthedocs.search.indexes import Index, ProjectIndex, PageIndex, SectionIndex

fake = Faker()


@pytest.fixture(autouse=True)
def mock_elastic_index(mocker):
    mocker.patch.object(Index, '_index', fake.word().lower())


@pytest.fixture(autouse=True)
@pytest.fixture
def search():
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
def project():
    return G(Project)


@pytest.fixture
def page_json():
    version_contents = {}

    def create_dummy_json():
        data = {
            'path': fake.word(),
            'title': fake.sentence(),
            'content': fake.text(),
            'sections': fake.sentences(),
            'headers': fake.sentences()
        }
        return data

    def get_dummy_json(version, *args, **kwargs):
        """Get dummy json content for a version page"""

        # Check existing content of that version
        # If not exist, generate new dummy content
        content = version_contents.get(version.id)
        if not content:
            content = create_dummy_json()
            # save in order to not regenerate dummy content for same version
            version_contents[version.id] = content

        return [content]

    return get_dummy_json


@pytest.fixture
def mock_parse_json(mocker, page_json):

    # patch the function from `projects.tasks` because it has been point to there
    # http://www.voidspace.org.uk/python/mock/patch.html#where-to-patch
    mocked_function = mocker.patch('readthedocs.projects.tasks.process_all_json_files')
    mocked_function.side_effect = page_json
