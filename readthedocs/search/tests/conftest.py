import json
import pytest
from django_dynamic_fixture import G
from faker import Faker

from readthedocs.builds.models import Version
from readthedocs.search.indexes import Index, ProjectIndex, PageIndex, SectionIndex

fake = Faker()


@pytest.fixture(autouse=True)
def mock_elastic_index(mocker):
    mocker.patch.object(Index, '_index', fake.word())


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

    yield
    index.delete_index(index_name=index_name)


@pytest.fixture
def make_page_content():

    def make_content():
        data = {
            'current_page_name': fake.sentence(),
            'title': fake.sentence(),
            'body': fake.text(),
            'toc': fake.text()
        }
        return data

    yield make_content


@pytest.fixture
def make_page_file(make_page_content, make_temp_json_dir):
    def make_file():
        page_content = make_page_content()
        file_name = fake.file_name(extension='fjson')
        directory = make_temp_json_dir()
        file_path = directory.join(file_name)
        with open(str(file_path), 'w') as f:
            json.dump(page_content, f)

        return directory
    return make_file


@pytest.fixture
def make_temp_json_dir(tmpdir_factory):
    def make_dir():
        return tmpdir_factory.mktemp('json')

    return make_dir


@pytest.mark.django_db
@pytest.fixture
def version():
    name = fake.name()
    return G(Version, project__name=str(name))


@pytest.fixture
def project(version, mocker, make_page_file):
    project = version.project
    media_path = mocker.patch('readthedocs.projects.models.Project.get_production_media_path')
    media_path.return_value = str(make_page_file())
    print project.get_production_media_path()
    return version.project