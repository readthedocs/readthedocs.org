"""Subversion-related utilities."""

import csv
from io import StringIO

from django.conf import settings

from readthedocs.projects.exceptions import RepositoryError
from readthedocs.vcs_support.base import BaseVCS, Deprecated, VCSVersion


class Backend(Deprecated, BaseVCS):

    """Subversion VCS backend."""

    supports_tags = False
    fallback_branch = "/trunk/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.repo_url[-1] != "/":
            self.base_url = self.repo_url
            self.repo_url += "/"
        elif self.repo_url.endswith("/trunk/"):
            self.supports_tags = True
            self.base_url = self.repo_url[:-7]
        else:
            self.base_url = self.repo_url

    def update(self):
        super().update()
        return self.co()

    def co(self, identifier=None):
        self.make_clean_working_dir()
        if identifier:
            url = self.get_url(self.base_url, identifier)
        else:
            url = self.repo_url
        retcode, out, err = self.run("svn", "checkout", url, ".")
        if retcode != 0:
            message_id = RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_NOT_ALLOWED
            if settings.ALLOW_PRIVATE_REPOS:
                message_id = RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_ALLOWED
            raise RepositoryError(message_id=message_id)
        return retcode, out, err

    @property
    def tags(self):
        retcode, stdout = self.run(
            "svn",
            "list",
            "%s/tags/" % self.base_url,
            record_as_success=True,
        )[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_tags(stdout)

    def parse_tags(self, data):
        """
        Parses output of svn list.

        Example:

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
        raw_tags = csv.reader(StringIO(data), delimiter="/")
        vcs_tags = []
        for name, _ in raw_tags:
            vcs_tags.append(VCSVersion(self, "/tags/%s/" % name, name))
        return vcs_tags

    @property
    def commit(self):
        _, stdout = self.run("svnversion")[:2]
        return stdout.strip()

    def checkout(self, identifier=None):
        super().checkout()
        return self.co(identifier)

    def get_url(self, base_url, identifier):
        base = base_url.rstrip("/")
        tag = identifier.lstrip("/")
        url = "{}/{}".format(base, tag)
        return url
