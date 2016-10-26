import os
import requests

from django.core.management.base import BaseCommand

from readthedocs.projects.models import Project
from readthedocs.projects.constants import GITHUB_REGEXS, PROGRAMMING_LANGUAGES

PL_DICT = {}

for slug, name in PROGRAMMING_LANGUAGES:
    PL_DICT[name] = slug


class Command(BaseCommand):
    """
    Import a project's programming language from GitHub.

    This builds a basic management command that will set
    a projects language to the most used one in GitHub.

    Requies a ``GITHUB_AUTH_TOKEN`` to be set in the environment,
    which should contain a proper GitHub Oauth Token for rate limiting.
    """

    def handle(self, *args, **options):
        token = os.environ.get('GITHUB_AUTH_TOKEN')
        if not token:
            print 'Invalid GitHub token, exiting'
            return

        for project in Project.objects.filter(programming_language__in=['none', '', 'words']):
            user = repo = ''
            repo_url = project.repo
            for regex in GITHUB_REGEXS:
                match = regex.search(repo_url)
                if match:
                    user, repo = match.groups()
                    break

            if not user:
                print 'No GitHub repo for %s' % repo_url
                continue

            url = 'https://api.github.com/repos/{user}/{repo}/languages'.format(
                user=user,
                repo=repo,
            )
            # We need this to get around GitHub's rate limiting
            headers = {'Authorization': 'token {token}'.format(token=token)}
            resp = requests.get(url, headers=headers)
            languages = resp.json()
            sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
            print 'Sorted langs: %s ' % sorted_langs
            top_lang = sorted_langs[0][0]
            if top_lang in PL_DICT:
                slug = PL_DICT[top_lang]
                print 'Setting %s to %s' % (repo_url, slug)
                project.programming_language = slug
                project.save()
            else:
                print 'Language unknown: %s' % top_lang
