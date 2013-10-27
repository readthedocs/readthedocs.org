import json

# Mock tastypi API.

class ProjectData(object):
    def get(self):
        return dict()


def mockVersion(repo):
    class MockVersion(object):
        def __init__(self, x=None):
            pass

        def put(self, x=None):
            return x

        def get(self, **kwargs):
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
                    "copyright": "",
                    "crate_url": "",
                    "default_branch": "",
                    "default_version": "latest",
                    "description": "Make docs.readthedocs.org work :D",
                    "django_packages_url": "",
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
                    "subdomain": "http://docs.readthedocs.org/",
                    "suffix": ".rst",
                    "theme": "default",
                    "use_virtualenv": false,
                    "users": [
                        "/api/v1/user/1/"
                    ],
                    "version": ""
                }""")
            version['project'] = project
            project['repo'] = repo
            if 'slug' in kwargs:
                return {'objects': [version], 'project': project}
            else:
              return version
    return MockVersion


class MockApi(object):
    def __init__(self, repo):
        self.version = mockVersion(repo)

    def project(self, x):
        return ProjectData()
