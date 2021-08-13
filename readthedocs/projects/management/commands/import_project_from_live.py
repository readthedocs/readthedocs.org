"""Import project command."""

import json
import os

import requests
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from ...models import Project


class Command(BaseCommand):

    """
    Import project from production API.

    This is a helper to debug issues with projects on the server more easily
    locally. It allows you to import projects based on the data that the public
    API provides.
    """

    help = (
        "Retrieves the data of a project from readthedocs.org's API and puts "
        'it into the local database. This is mostly useful for debugging '
        'issues with projects on the live site.'
    )

    def add_arguments(self, parser):
        parser.add_argument('project_slug', nargs='+', type=str)

    def handle(self, *args, **options):
        auth = None
        user1 = User.objects.filter(pk__gt=0).order_by('pk').first()

        if 'READTHEDOCS_USERNAME' in os.environ and 'READTHEDOCS_PASSWORD' in os.environ:
            # Authenticating allows returning additional useful fields in the API
            # See: `ProjectAdminSerializer`
            username = os.environ['READTHEDOCS_USERNAME']
            auth = (username, os.environ['READTHEDOCS_PASSWORD'])
            self.stdout.write('Using basic auth for user {username}'.format(username=username))

        for slug in options['project_slug']:
            self.stdout.write('Importing {slug} ...'.format(slug=slug))

            resp = requests.get(
                'https://readthedocs.org/api/v2/project/',
                params={'slug': slug},
                auth=auth,
            )
            resp.raise_for_status()  # This should only fail if RTD is having issues
            response_data = resp.json()

            if response_data['count'] == 1:
                project_data = response_data['results'][0]
            else:
                raise CommandError(
                    'Cannot find {slug} in API. Response was:\n{response}'.format(
                        slug=slug,
                        response=json.dumps(response_data),
                    ),
                )

            try:
                project = Project.objects.get(slug=slug)
                self.stdout.write('Project {slug} already exists. Updating...'.format(slug=slug))
            except Project.DoesNotExist:
                project = Project(slug=slug)

            exclude_attributes = (
                'absolute_url',
                'analytics_code',
                'canonical_url',
                'show_advertising',

                # These fields could be nice to add
                'users',
                'features',
                'environment_variables',
            )

            for attribute in project_data:
                if attribute not in exclude_attributes:
                    setattr(project, attribute, project_data[attribute])
                    self.stdout.write(' - Setting {key} to {val}'.format(
                        key=attribute,
                        val=project_data[attribute]),
                    )
            project.user = user1
            project.save()
            if user1:
                project.users.add(user1)

            call_command('update_repos', slugs=[project.slug], version='all')
