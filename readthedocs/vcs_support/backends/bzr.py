"""Bazaar-related utilities."""

import csv
import re
from io import StringIO

from readthedocs.projects.exceptions import RepositoryError
from readthedocs.vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):

    """Bazaar VCS backend."""

    supports_tags = True
    fallback_branch = ""

    def clone(self):
        self.make_clean_working_dir()
        try:
            self.run("bzr", "checkout", self.repo_url, ".")
        except RepositoryError:
            raise RepositoryError(RepositoryError.CLONE_ERROR())

    @property
    def tags(self):
        try:
            code, stdout, stderr = self.run("bzr", "tags", record_as_success=True)
            return self.parse_tags(stdout)
        except RepositoryError:
            # error (or no tags found)
            return []

    def parse_tags(self, data):
        """
        Parses output of bzr tags.

        Example:

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
        squashed_data = re.sub(r" +", " ", data)
        raw_tags = csv.reader(StringIO(squashed_data), delimiter=" ")
        vcs_tags = []
        for row in raw_tags:
            name = " ".join(row[:-1])
            commit = row[-1]
            if commit != "?":
                vcs_tags.append(VCSVersion(self, commit, name))
        return vcs_tags

    @property
    def commit(self):
        _, stdout, _ = self.run("bzr", "revno")
        return stdout.strip()

    def checkout(self, identifier=None):
        super().checkout()

        if not identifier:
            return self.up()

        try:
            code, stdout, stderr = self.run("bzr", "switch", identifier)
            return code, stdout, stderr
        except RepositoryError:
            raise RepositoryError(
                RepositoryError.FAILED_TO_CHECKOUT.format(identifier),
            )
