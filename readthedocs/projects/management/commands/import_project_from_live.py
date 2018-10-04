"""Import project command"""

from __future__ import absolute_import
from django.core.management import call_command
from django.core.management.base import BaseCommand
import json
import slumber

from django.contrib.auth.models import User
from ...models import Project


class Command(BaseCommand):

    """
    Import project from production API

    This is a helper to debug issues with projects on the server more easily
    locally. It allows you to import projects based on the data that the public
    API provides.
    """

    help = (
        "Retrieves the data of a project from readthedocs.org's API and puts "
        "it into the local database. This is mostly useful for debugging "
        "issues with projects on the live site."
    )

    def add_arguments(self, parser):
        parser.add_argument('project_slug', nargs='+', type=str)

    def handle(self, *args, **options):
        api = slumber.API(base_url='http://readthedocs.org/api/v1/')
        user1 = User.objects.filter(pk__gt=0).order_by('pk').first()

        for slug in options['project_slug']:
            self.stdout.write('Importing {slug} ...'.format(slug=slug))

            project_data = api.project.get(slug=slug)
            try:
                project_data = project_data['objects'][0]
            except (KeyError, IndexError):
                self.stderr.write(
                    'Cannot find {slug} in API. Response was:\n{response}'
                    .format(
                        slug=slug,
                        response=json.dumps(project_data)))

            try:
                project = Project.objects.get(slug=slug)
            except Project.DoesNotExist:
                project = Project(slug=slug)

            exclude_attributes = (
                'absolute_url',
                'analytics_code',
                'canonical_url',
                'users',
            )

            for attribute in project_data:
                if attribute not in exclude_attributes:
                    setattr(project, attribute, project_data[attribute])
            project.user = user1
            project.save()
            if user1:
                project.users.add(user1)

            call_command('update_repos', project.slug, version='all')
