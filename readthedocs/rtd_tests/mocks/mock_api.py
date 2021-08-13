"""Mock versions of many API-related classes."""
import json
from contextlib import contextmanager

from unittest import mock


# Mock tastypi API.


class ProjectData:
    def get(self):
        return {}

    def put(self, x=None):
        return x


def mock_version(repo):
    """Construct and return a class implementing the Version interface."""
    class MockVersion:
        def __init__(self, x=None):
            pass

        def put(self, x=None):
            return x

        def get(self, **kwargs):
            """Returns mock data to emulate real Version objects."""
            # SCIENTIST DOG
            version = json.loads("""
                {
                    "active": false,
                    "built": false,
                    "id": "12095",
                    "identifier": "remotes/origin/zip_importing",
                    "resource_uri": "/api/v1/version/12095/",
                    "slug": "zip_importing",
                    "uploaded": false,
                    "verbose_name": "zip_importing"
                }""")

            project = json.loads("""
                {
                    "absolute_url": "/projects/docs/",
                    "analytics_code": "",
                    "default_branch": "",
                    "default_version": "latest",
                    "description": "Make docs.readthedocs.org work :D",
                    "documentation_type": "sphinx",
                    "id": "2599",
                    "modified_date": "2012-03-12T19:59:09.130773",
                    "name": "docs",
                    "project_url": "",
                    "pub_date": "2012-02-19T18:10:56.582780",
                    "repo": "git://github.com/rtfd/readthedocs.org",
                    "repo_type": "git",
                    "requirements_file": "",
                    "resource_uri": "/api/v1/project/2599/",
                    "slug": "docs",
                    "install_project": false,
                    "users": [
                        "/api/v1/user/1/"
                    ]
                }""")
            version['project'] = project
            project['repo'] = repo
            if 'slug' in kwargs:
                return {'objects': [version], 'project': project}
            return version
    return MockVersion


class MockApi:
    def __init__(self, repo):
        self.version = mock_version(repo)

    def project(self, _):
        return ProjectData()

    def build(self, _):
        return mock.Mock(**{'get.return_value': {'id': 123, 'state': 'triggered'}})

    def command(self, _):
        return mock.Mock(**{'get.return_value': {}})


@contextmanager
def mock_api(repo):
    api_mock = MockApi(repo)
    with mock.patch('readthedocs.api.v2.client.api', api_mock), \
            mock.patch('readthedocs.projects.tasks.api_v2', api_mock), \
            mock.patch('readthedocs.doc_builder.environments.api_v2', api_mock):
        yield api_mock
