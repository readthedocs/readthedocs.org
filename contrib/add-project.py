"""
Script to add a Git project as cloned from a Github repository
to ReadTheDocs. Invoke from the checkout.
"""

__requires__ = ['requests-toolbelt', 'autocommand', 'keyring']


import os
import getpass
import re
import urllib.parse
import subprocess
import pathlib

import autocommand
import keyring
from requests_toolbelt import sessions


rtd = sessions.BaseUrlSession(
    os.environ.get('RTD_URL', 'https://readthedocs.org/api/v2/'))
github = sessions.BaseUrlSession('https://api.github.com/')
github.headers.update(Accept='application/vnd.github.v3+json')


class User:
    """
    A User (with a password) in RTD.

    Resolves username using ``getpass.getuser()``. Override with
    RTD_USERNAME environment variable.

    Resolves password using keyring. Install keyring and run
    ``keyring set https://readthedocs.org/ $USER`` to set the pw.
    Override with RTD_PASSWORD environment variable.
    """
    def __init__(self):
        self.name = os.environ.get('RTD_USERNAME') or getpass.getuser()
        system = rtd.create_url('/')
        self.password = (
            os.environ.get('RTD_PASSWORD')
            or keyring.get_password(system, self.name)
        )

    @property
    def id(self):
        resp = rtd.get('../v1/user/', params=dict(username=self.name))
        resp.raise_for_status()
        ob, = resp.json()['objects']
        return ob['id']

    @property
    def tuple(self):
        return self.name, self.password


class Sluggable(str):
    """
    A name for use in RTD with a 'slug' version.
    """
    @property
    def slug(self):
        return self.replace('.', '')


class Repo:
    """
    A Git repo
    """

    def __init__(self, root):
        self.root = root
        cmd = ['git', '-C', root, 'remote', 'get-url', 'origin']
        proc = subprocess.run(
            cmd, check=True, text=True, stdout=subprocess.PIPE)
        self.url = proc.stdout.strip()

    @property
    def name(self):
        return Sluggable(pathlib.Path(self.url).stem)


def create_project(repo):
    """
    Create the project from a Repo
    """
    user = User()
    payload = dict(
        repo=repo.url,
        slug=repo.name.slug,
        name=repo.name,
        users=[user.id],
    )
    resp = rtd.post('project/', json=payload, auth=user.tuple)
    resp.raise_for_status()


def configure_github(name, url):
    """
    Given a project name and webhook URL, configure the webhook
    in GitHub.

    Resolves username from ``getpass.getuser()``. Override with
    ``GITHUB_USERNAME``.

    Resolves access token from keyring for username and system
    'github.com'. Override with ``GITHUB_TOKEN`` environment
    variable.
    """
    user = os.environ.get('GITHUB_USERNAME') or getpass.getuser()
    token = (
        keyring.get_password('github.com', user)
        or os.environ['GITHUB_TOKEN']
    )
    headers = dict(Authorization=f'token {token}')
    path = f'/repos/{user}/{name}/hooks'
    params = dict(
        name='web',
        config=dict(
            url=url,
            content_type='json',
        ),
    )
    github.post(path, json=params, headers=headers)


def configure_webhook(name):
    """
    Identify the webhook URL for a RTD project named name.
    """
    login_path = '/accounts/login/'
    resp = rtd.get(login_path)
    token = rtd.cookies.get('csrftoken') or rtd.cookies['csrf']
    user = User()
    params = dict(
        login=user.name,
        password=user.password,
        csrfmiddlewaretoken=token,
        next='/',
    )
    headers = dict(Referer=rtd.create_url(login_path))
    resp = rtd.post(login_path, data=params, headers=headers)
    token = rtd.cookies.get('csrftoken') or rtd.cookies['csrf']
    params = dict(
        integration_type='github_webhook',
        csrfmiddlewaretoken=token,
        next='/',
    )
    create_path = f'/dashboard/{name.slug}/integrations/create/'
    headers = dict(
        Referer=rtd.create_url(create_path),
    )
    resp = rtd.post(
        create_path,
        data=params,
        headers=headers,
    )
    resp.raise_for_status()
    ref = re.search(f'<a href="(.*?)">.*?webhook.*?</a>', resp.text).group(1)
    return urllib.parse.urljoin(resp.url, ref)


@autocommand.autocommand(__name__)
def main(repo: Repo = Repo('.')):
    create_project(repo)
    url = configure_webhook(repo.name)
    configure_github(repo.name, url)
