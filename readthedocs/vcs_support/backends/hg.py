
"""Mercurial-related utilities."""
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):

    """Mercurial VCS backend."""

    supports_tags = True
    supports_branches = True
    fallback_branch = 'default'

    def update(self):
        super().update()
        if self.repo_exists():
            return self.pull()
        return self.clone()

    def repo_exists(self):
        try:
            code, _, _ = self.run('hg', 'status', record=False)
            return code == 0
        except RepositoryError:
            return False

    def pull(self):
        self.run('hg', 'pull')
        code, stdout, stderr = self.run('hg', 'update', '--clean')
        return code, stdout, stderr

    def clone(self):
        self.make_clean_working_dir()
        try:
            # Disable sparse-revlog extension when cloning because it's not
            # included in older versions of Mercurial and producess an error
            # when using an old version. See
            # https://github.com/readthedocs/readthedocs.org/pull/9042/

            output = self.run(
                "hg", "clone", "--config", "format.sparse-revlog=no", self.repo_url, "."
            )
            return output
        except RepositoryError:
            raise RepositoryError(RepositoryError.CLONE_ERROR)

    @property
    def branches(self):
        try:
            _, stdout, _ = self.run(
                'hg',
                'branches',
                '--quiet',
                record_as_success=True,
            )
            return self.parse_branches(stdout)
        except RepositoryError:
            # error (or no tags found)
            return []

    def parse_branches(self, data):
        """
        Parses output of `hg branches --quiet`.

        Example:

            default
            0.2
            0.1

        Into VCSVersion objects with branch name as verbose_name and
        identifier.
        """
        names = [name.lstrip() for name in data.splitlines()]
        return [VCSVersion(self, name, name) for name in names if name]

    @property
    def tags(self):
        try:
            _, stdout, _ = self.run('hg', 'tags', record_as_success=True)
            return self.parse_tags(stdout)
        except RepositoryError:
            # error (or no tags found)
            return []

    def parse_tags(self, data):
        """
        Parses output of `hg tags`.

        Example:

            tip                              278:c4b2d21db51a
            0.2.2                            152:6b0364d98837
            0.2.1                            117:a14b7b6ffa03
            0.1                               50:30c2c6b3a055
            maintenance release 1             10:f83c32fe8126

        Into VCSVersion objects with the tag name as verbose_name and the
        commit hash as identifier.
        """
        vcs_tags = []
        tag_lines = [line.strip() for line in data.splitlines()]
        # starting from the rhs of each line, split a single value (changeset)
        # off at whitespace; the tag name is the string to the left of that
        tag_pairs = [line.rsplit(None, 1) for line in tag_lines]
        for row in tag_pairs:
            if len(row) != 2:
                continue
            name, commit = row
            if name == 'tip':
                continue
            _, commit_hash = commit.split(':')
            vcs_tags.append(VCSVersion(self, commit_hash, name))
        return vcs_tags

    @property
    def commit(self):
        _, stdout = self.run('hg', 'identify', '--id')[:2]
        return stdout.strip()

    def checkout(self, identifier=None):
        super().checkout()
        if not identifier:
            identifier = 'tip'

        try:
            code, stdout, stderr = self.run(
                'hg',
                'update',
                '--clean',
                identifier,
            )
            return code, stdout, stderr
        except RepositoryError:
            raise RepositoryError(
                RepositoryError.FAILED_TO_CHECKOUT.format(identifier),
            )
