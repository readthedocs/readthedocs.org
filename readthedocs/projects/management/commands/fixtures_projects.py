"""
Fixture Projects

This command intends to replace the fixtures file
which is used and instead create projects directly.

"""

from django.core.management.base import BaseCommand

from readthedocs.projects.models import Project


class Command(BaseCommand):

    help = __doc__

    def load_data(self):
        projects = [
            ("Read The Docs", "https://github.com/rtfd/readthedocs.org"),
            ("Django Test Utils", "https://github.com/ericholscher/django-test-utils"),
            ("Fabric", "https://github.com/fabric/fabric"),
            ("South", "http://github.com/dmishe/django-south"),
            ("Pip", "https://github.com/pypa/pip"),
            ("Kong", "https://github.com/ericholscher/django-kong"),
            ("Djangoembed", "https://github.com/worldcompany/djangoembed"),
            ("Tastypie", "http://github.com/codysoyland/django-tastypie"),
            ("Django Uni Form", "https://github.com/pydanny/django-uni-form"),
            ("Cue", "http://github.com/coleifer/cue.git"),
            ("Pinax", "http://github.com/pinax/pinax"),
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

    def handle(self, *args, **kwargs):
        self.load_data()
        self.stdout.write("Loaded data")
