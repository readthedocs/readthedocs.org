# -*- coding: utf-8 -*-
"""Subversion-related utilities."""

from __future__ import absolute_import

import csv

from builtins import str
from six import StringIO  # noqa

from readthedocs.projects.exceptions import RepositoryError
from readthedocs.vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):

    """Subversion VCS backend."""

    supports_tags = False
    fallback_branch = '/trunk/'

    def __init__(self, project, version, **kwargs):
        super(Backend, self).__init__(project, version)
        if self.repo_url[-1] != '/':
            self.base_url = self.repo_url
            self.repo_url += '/'
        elif self.repo_url.endswith('/trunk/'):
            self.supports_tags = True
            self.base_url = self.repo_url[:-7]
        else:
            self.base_url = self.repo_url

    def update(self):
        super(Backend, self).update()
        # For some reason `svn status` gives me retcode 0 in non-svn
        # directories that's why I use `svn info` here.
        retcode = self.run('svn', 'info', force_success=True)[0]
        if retcode == 0:
            self.up()
        else:
            self.co()

    def up(self):
        retcode = self.run('svn', 'revert', '--recursive', '.')[0]
        if retcode != 0:
            raise RepositoryError
        retcode, out, err = self.run(
            'svn', 'up', '--accept', 'theirs-full',
            '--trust-server-cert', '--non-interactive')
        if retcode != 0:
            raise RepositoryError
        return retcode, out, err

    def co(self, identifier=None):
        self.make_clean_working_dir()
        if identifier:
            url = self.base_url + identifier
        else:
            url = self.repo_url
        retcode, out, err = self.run('svn', 'checkout', url, '.')
        if retcode != 0:
            raise RepositoryError
        return retcode, out, err

    @property
    def tags(self):
        retcode, stdout = self.run('svn', 'list', '%s/tags/'
                                   % self.base_url, force_success=True)[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_tags(stdout)

    def parse_tags(self, data):
        """
        Parses output of svn list, eg:

            release-1.1/
            release-1.2/
            release-1.3/
            release-1.4/
            release-1.4.1/
            release-1.5/
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        # StringIO below is expecting Unicode data, so ensure that it gets it.
        if not isinstance(data, str):
            data = str(data)
        raw_tags = csv.reader(StringIO(data), delimiter='/')
        vcs_tags = []
        for name, _ in raw_tags:
            vcs_tags.append(VCSVersion(self, '/tags/%s/' % name, name))
        return vcs_tags

    @property
    def commit(self):
        _, stdout = self.run('svnversion')[:2]
        return stdout.strip()

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        retcode = self.run('svn', 'info', record=False)[0]
        if retcode == 0:
            result = self.up()
        else:
            result = self.co(identifier)
        # result is (return_code, stdout, stderr)
        return result
