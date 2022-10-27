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
            ("Read The Docs", "https://github.com/rtfd/readthedocs.org"),
            ("Django Test Utils", "https://github.com/ericholscher/django-test-utils"),
            ("Fabric", "https://github.com/fabric/fabric"),
            ("South", "https://github.com/dmishe/django-south"),
            ("Pip", "https://github.com/pypa/pip"),
            ("Kong", "https://github.com/ericholscher/django-kong"),
            ("Djangoembed", "https://github.com/worldcompany/djangoembed"),
            ("Tastypie", "https://github.com/codysoyland/django-tastypie"),
            ("Django Uni Form", "https://github.com/pydanny/django-uni-form"),
            ("Cue", "https://github.com/coleifer/cue.git"),
            ("Pinax", "https://github.com/pinax/pinax"),
            ("Haystack", "https://github.com/toastdriven/django-haystack"),
            ("Taggit", "https://github.com/alex/django-taggit"),
            ("test_project", "https://github.com/bogususer/non-existing-repo"),
            ("Sphinx", "https://github.com/sphinx-doc/sphinx"),
            ("Numpy", "https://github.com/numpy/numpy"),
            ("Conda", "https://github.com/conda/conda"),
        ]
        for name, repo in projects:
            Project.objects.get_or_create(
                name=name,
                slug=name.replace(" ", "-").lower(),
                repo=repo,
                repo_type="git",
            )

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
        # Read the doc versions
        rtd = Project.objects.get(slug="read-the-docs")
        for type, identifier, verbose_name, slug in [
            ("unknown", "2ff3d36340fa4d3d39424e8464864ca37c5f191c", "0.2.1", "0.2.1"),
            ("unknown", "354456a7dba2a75888e2fe91f6d921e5fe492bcd", "0.2.2", "0.2.2"),
            ("unknown", "master", "latest", "latest"),
            ("unknown", "not_ok", "not_ok", "not_ok"),
            ("unknown", "awesome", "awesome", "awesome"),
        ]:
            Version.objects.get_or_create(
                project=rtd,
                type=type,
                identifier=identifier,
                verbose_name=verbose_name,
                slug=slug,
            )

        # Pip versions
        pip = Project.objects.get(slug="pip")
        for type, identifier, verbose_name, slug in [
            ("tag", "2404a34eba4ee9c48cc8bc4055b99a48354f4950", "0.8", "0.8"),
            ("tag", "f55c28e560c92cafb6e6451f8084232b6d717603", "0.8.1", "0.8.1"),
        ]:
            Version.objects.get_or_create(
                project=pip,
                type=type,
                identifier=identifier,
                verbose_name=verbose_name,
                slug=slug,
            )

        # Versions for sphinx, numpy and conda
        sphinx = Project.objects.get(slug="sphinx")
        numpy = Project.objects.get(slug="numpy")
        conda = Project.objects.get(slug="conda")

        for project, type, identifier, verbose_name, slug in [
            (sphinx, "branch", "master", "latest", "latest"),
            (numpy, "branch", "master", "latest", "latest"),
            (conda, "branch", "master", "latest", "latest"),
        ]:
            Version.objects.get_or_create(
                project=project,
                type=type,
                identifier=identifier,
                verbose_name=verbose_name,
                slug=slug,
            )

    def handle(self, *args, **kwargs):
        self.load_data()
        self.stdout.write("Loaded data")
