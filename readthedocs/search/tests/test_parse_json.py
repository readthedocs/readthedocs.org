import json
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest
from django_dynamic_fixture import get

from readthedocs.builds.storage import BuildMediaFileSystemStorage
from readthedocs.projects.constants import MKDOCS, SPHINX
from readthedocs.projects.models import HTMLFile, Project

data_path = Path(__file__).parent.resolve() / 'data'


@pytest.mark.django_db
@pytest.mark.search
class TestParseJSON:

    def setup_method(self):
        self.project = get(
            Project,
            slug='test',
            main_language_project=None,
        )
        self.version = self.project.versions.first()

    def _mock_open(self, content):
        @contextmanager
        def f(*args, **kwargs):
            read_mock = mock.MagicMock()
            read_mock.read.return_value = content
            yield read_mock
        return f

    @mock.patch.object(BuildMediaFileSystemStorage, 'exists')
    @mock.patch.object(BuildMediaFileSystemStorage, 'open')
    def test_mkdocs(self, storage_open, storage_exists):
        json_file = data_path / 'mkdocs/in/search_index.json'
        storage_open.side_effect = self._mock_open(
            json_file.open().read()
        )
        storage_exists.return_value = True

        self.version.documentation_type = MKDOCS
        self.version.save()

        index_file = get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path='index.html',
        )
        versions_file = get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path='versions/index.html',
        )
        no_title_file = get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path='no-title/index.html',
        )

        parsed_json = [
            index_file.processed_json,
            versions_file.processed_json,
            no_title_file.processed_json,
        ]
        expected_json = json.load(open(data_path / 'mkdocs/out/search_index.json'))
        assert parsed_json == expected_json

    @mock.patch.object(BuildMediaFileSystemStorage, 'exists')
    @mock.patch.object(BuildMediaFileSystemStorage, 'open')
    def test_mkdocs_old_version(self, storage_open, storage_exists):
        json_file = data_path / 'mkdocs/in/search_index_old.json'
        storage_open.side_effect = self._mock_open(
            json_file.open().read()
        )
        storage_exists.return_value = True

        self.version.documentation_type = MKDOCS
        self.version.save()

        index_file = get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path='index.html',
        )
        versions_file = get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path='versions/index.html',
        )

        parsed_json = [
            index_file.processed_json,
            versions_file.processed_json,
        ]
        expected_json = json.load(open(data_path / 'mkdocs/out/search_index_old.json'))
        assert parsed_json == expected_json

    @mock.patch.object(BuildMediaFileSystemStorage, 'exists')
    @mock.patch.object(BuildMediaFileSystemStorage, 'open')
    def test_sphinx(self, storage_open, storage_exists):
        json_file = data_path / 'sphinx/in/page.json'
        html_content = data_path / 'sphinx/in/page.html'

        json_content = json.load(json_file.open())
        json_content['body'] = html_content.open().read()
        storage_open.side_effect = self._mock_open(
            json.dumps(json_content)
        )
        storage_exists.return_value = True

        self.version.documentation_type = SPHINX
        self.version.save()

        page_file = get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path='page.html',
        )

        parsed_json = page_file.processed_json
        expected_json = json.load(open(data_path / 'sphinx/out/page.json'))
        assert parsed_json == expected_json

    @mock.patch.object(BuildMediaFileSystemStorage, 'exists')
    @mock.patch.object(BuildMediaFileSystemStorage, 'open')
    def test_sphinx_page_without_title(self, storage_open, storage_exists):
        json_file = data_path / 'sphinx/in/no-title.json'
        html_content = data_path / 'sphinx/in/no-title.html'

        json_content = json.load(json_file.open())
        json_content['body'] = html_content.open().read()
        storage_open.side_effect = self._mock_open(
            json.dumps(json_content)
        )
        storage_exists.return_value = True

        self.version.documentation_type = SPHINX
        self.version.save()

        page_file = get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path='no-title.html',
        )

        parsed_json = page_file.processed_json
        expected_json = json.load(open(data_path / 'sphinx/out/no-title.json'))
        assert parsed_json == expected_json
