# -*- coding: utf-8 -*-
"""Bazaar-related utilities."""

from __future__ import absolute_import

import csv
import re

from builtins import bytes, str  # pylint: disable=redefined-builtin
from six import StringIO

from readthedocs.projects.exceptions import RepositoryError
from readthedocs.vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):

    """Bazaar VCS backend."""

    supports_tags = True
    fallback_branch = ''

    def update(self):
        super(Backend, self).update()
        retcode = self.run('bzr', 'status', warn_only=True)[0]
        if retcode == 0:
            self.up()
        else:
            self.clone()

    def up(self):
        retcode = self.run('bzr', 'revert')[0]
        if retcode != 0:
            raise RepositoryError
        up_output = self.run('bzr', 'up')
        if up_output[0] != 0:
            raise RepositoryError
        return up_output

    def clone(self):
        self.make_clean_working_dir()
        retcode = self.run('bzr', 'checkout', self.repo_url, '.')[0]
        if retcode != 0:
            raise RepositoryError

    @property
    def tags(self):
        retcode, stdout = self.run('bzr', 'tags', warn_only=True)[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_tags(stdout)

    def parse_tags(self, data):
        """
        Parses output of bzr tags, eg:

            0.1.0                171
            0.1.1                173
            0.1.2                174
            0.2.0-pre-alpha      177

        Can't forget about poorly formatted tags or tags that lack revisions,
        such as:

            3.3.0-rc1            ?
            tag with spaces      123
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        # StringIO below is expecting Unicode data, so ensure that it gets it.
        if not isinstance(data, str):
            data = str(data)
        squashed_data = re.sub(r' +', ' ', data)
        raw_tags = csv.reader(StringIO(squashed_data), delimiter=' ')
        vcs_tags = []
        for row in raw_tags:
            name = ' '.join(row[:-1])
            commit = row[-1]
            if commit != '?':
                vcs_tags.append(VCSVersion(self, commit, name))
        return vcs_tags

    @property
    def commit(self):
        _, stdout = self.run('bzr', 'revno')[:2]
        return stdout.strip()

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        self.update()
        if not identifier:
            return self.up()
        return self.run('bzr', 'switch', identifier)
