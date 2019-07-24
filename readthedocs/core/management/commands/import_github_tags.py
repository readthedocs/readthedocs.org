"""
Import a project's tags from GitHub.

Requires a ``GITHUB_AUTH_TOKEN`` to be set in the environment.
This should be a "Personal access token" although no permissions are required.
With the token, the rate limit is increased to 5,000 requests/hour

https://github.com/settings/tokens
https://developer.github.com/v3/#rate-limiting
"""

import os
import time

import requests
from django.core.management.base import BaseCommand, CommandError

from readthedocs.projects.constants import GITHUB_REGEXS
from readthedocs.projects.models import Project


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        token = os.environ.get('GITHUB_AUTH_TOKEN')
        if not token:
            raise CommandError('Invalid GitHub token, exiting...')

        queryset = Project.objects.filter(tags=None).filter(repo__contains='github.com')
        project_total = queryset.count()

        for i, project in enumerate(queryset.iterator()):
            # Get the user and repo name from the URL as required by GitHub's API
            user = repo = ''
            for regex in GITHUB_REGEXS:
                match = regex.search(project.repo)
                if match:
                    user, repo = match.groups()
                    break

            if not user:
                self.stderr.write(f'No GitHub repo for {project.repo}')
                continue

            # https://developer.github.com/v3/repos/#list-all-topics-for-a-repository
            url = 'https://api.github.com/repos/{user}/{repo}/topics'.format(
                user=user,
                repo=repo,
            )
            headers = {
                'Authorization': 'token {token}'.format(token=token),

                # Getting topics is a preview API and may change
                # It requires this custom Accept header
                'Accept': 'application/vnd.github.mercy-preview+json',
            }

            self.stdout.write(
                '[{}/{}] Fetching tags for {}'.format(i + 1, project_total, project.slug)
            )

            resp = requests.get(url, headers=headers)
            if resp.ok:
                tags = resp.json()['names']
                if tags:
                    self.stdout.write('Setting tags for {}: {}'.format(project.slug, tags))
                    project.tags.set(*tags)
            else:
                self.stderr.write('GitHub API error ({}): {}'.format(project.slug, resp.content))

            # Sleeping half a second should keep us under 5k requests/hour
            time.sleep(0.5)
