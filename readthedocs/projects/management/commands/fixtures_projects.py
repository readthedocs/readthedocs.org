"""
Fixture Projects.

This command intends to replace the fixtures file
which is used and instead create projects directly.

"""

from django.core.management.base import BaseCommand

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project, ProjectRelationship


class Command(BaseCommand):

    help = __doc__

    def load_data(self):
        projects = [
            {
                "name": "Read The Docs",
                "slug": "read-the-docs",
                "repo": "https://github.com/rtfd/readthedocs.org",
                "repo_type": "git",
            },
            {
                "name": "Django Test Utils",
                "slug": "django-test-utils",
                "repo": "https://github.com/ericholscher/django-test-utils",
                "repo_type": "git",
            },
            {
                "name": "Fabric",
                "slug": "fabric",
                "repo": "https://github.com/fabric/fabric",
                "repo_type": "git",
            },
            {
                "name": "South",
                "slug": "south",
                "repo": "https://github.com/dmishe/django-south",
                "repo_type": "git",
            },
            {
                "name": "Pip",
                "slug": "pip",
                "repo": "https://github.com/pypa/pip",
                "repo_type": "git",
            },
            {
                "name": "Kong",
                "slug": "kong",
                "repo": "https://github.com/ericholscher/django-kong",
                "repo_type": "git",
            },
            {
                "name": "Djangoembed",
                "slug": "djangoembed",
                "repo": "https://github.com/worldcompany/djangoembed",
                "repo_type": "git",
            },
            {
                "name": "Tastypie",
                "slug": "tastypie",
                "repo": "https://github.com/codysoyland/django-tastypie",
                "repo_type": "git",
            },
            {
                "name": "Django Uni Form",
                "slug": "django-uni-form",
                "repo": "https://github.com/pydanny/django-uni-form",
                "repo_type": "git",
            },
            {
                "name": "Cue",
                "slug": "cue",
                "repo": "https://github.com/coleifer/cue.git",
                "repo_type": "git",
            },
            {
                "name": "Pinax",
                "slug": "pinax",
                "repo": "https://github.com/pinax/pinax",
                "repo_type": "git",
            },
            {
                "name": "Haystack",
                "slug": "haystack",
                "repo": "https://github.com/toastdriven/django-haystack",
                "repo_type": "git",
            },
            {
                "name": "Taggit",
                "slug": "taggit",
                "repo": "https://github.com/alex/django-taggit",
                "repo_type": "git",
            },
            {
                "name": "test_project",
                "slug": "test_project",
                "repo": "https://github.com/bogususer/non-existing-repo",
                "repo_type": "git",
            },
            {
                "name": "Sphinx",
                "slug": "sphinx",
                "repo": "https://github.com/sphinx-doc/sphinx",
                "repo_type": "git",
            },
            {
                "name": "Numpy",
                "slug": "numpy",
                "repo": "https://github.com/numpy/numpy",
                "repo_type": "git",
            },
            {
                "name": "Conda",
                "slug": "conda",
                "repo": "https://github.com/conda/conda",
                "repo_type": "git",
            },
        ]

        for project in projects:
            Project.objects.get_or_create(**project)

        # Clear Version table since it gets populated with all "latest" slugs
        # Create specific Version objects matching the original fixtures test data
        Version.objects.all().delete()
        assert Version.objects.count() == 0
        # Create ProjectRelationship object
        parent = Project.objects.get(slug="pip")
        child = Project.objects.get(slug="test_project")

        ProjectRelationship.objects.get_or_create(
            parent=parent, child=child, alias=None
        )

        # Create only specific Version objects for projects readthedocs, pip, Sphinx, Numpy, Conda
        # Specific versions same as fixtures
        rtd = Project.objects.get(slug="read-the-docs")
        pip = Project.objects.get(slug="pip")
        sphinx = Project.objects.get(slug="sphinx")
        numpy = Project.objects.get(slug="numpy")
        conda = Project.objects.get(slug="conda")
        versions = [
            {
                "project": rtd,
                "type": "unknown",
                "identifier": "2ff3d36340fa4d3d39424e8464864ca37c5f191c",
                "verbose_name": "0.2.1",
                "slug": "0.2.1",
                "supported": True,
                "active": True,
                "built": True,
            },
            {
                "project": rtd,
                "type": "unknown",
                "identifier": "354456a7dba2a75888e2fe91f6d921e5fe492bcd",
                "verbose_name": "0.2.2",
                "slug": "0.2.2",
                "supported": True,
                "active": True,
                "built": True,
            },
            {
                "project": rtd,
                "type": "unknown",
                "identifier": "master",
                "verbose_name": "latest",
                "slug": "latest",
                "supported": True,
                "active": True,
                "built": True,
            },
            {
                "project": rtd,
                "type": "unknown",
                "identifier": "not_ok",
                "verbose_name": "not_ok",
                "slug": "not_ok",
                "supported": True,
                "active": False,
                "built": True,
            },
            {
                "project": rtd,
                "type": "unknown",
                "identifier": "awesome",
                "verbose_name": "awesome",
                "slug": "awesome",
                "supported": True,
                "active": True,
                "built": True,
            },
            {
                "project": pip,
                "type": "tag",
                "identifier": "2404a34eba4ee9c48cc8bc4055b99a48354f4950",
                "verbose_name": "0.8",
                "slug": "0.8",
                "supported": False,
                "active": True,
                "built": False,
            },
            {
                "project": pip,
                "type": "tag",
                "identifier": "f55c28e560c92cafb6e6451f8084232b6d717603",
                "verbose_name": "0.8.1",
                "slug": "0.8.1",
                "supported": False,
                "active": True,
                "built": False,
            },
            {
                "project": sphinx,
                "type": "branch",
                "identifier": "master",
                "verbose_name": "latest",
                "slug": "latest",
                "supported": True,
                "active": True,
                "built": False,
            },
            {
                "project": numpy,
                "type": "branch",
                "identifier": "master",
                "verbose_name": "latest",
                "slug": "latest",
                "supported": True,
                "active": True,
                "built": False,
            },
            {
                "project": conda,
                "type": "branch",
                "identifier": "master",
                "verbose_name": "latest",
                "slug": "latest",
                "supported": True,
                "active": True,
                "built": False,
            },
        ]

        for version in versions:
            Version.objects.get_or_create(**version)

    def handle(self, *args, **kwargs):
        self.load_data()
        self.stdout.write("Loaded data")
