from projects.exceptions import ProjectImportError
from vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):
    supports_tags = True
    supports_branches = True
    fallback_branch = 'default'

    def update(self):
        super(Backend, self).update()
        retcode = self.run('hg', 'status')[0]
        if retcode == 0:
            return self.pull()
        else:
            return self.clone()

    def pull(self):
        pull_output = self.run('hg', 'pull')
        if pull_output[0] != 0:
            raise ProjectImportError(
                ("Failed to get code from '%s' (hg pull): %s"
                 % (self.repo_url, pull_output[0]))
            )
        update_output = self.run('hg', 'update', '-C')[0]
        if update_output[0] != 0:
            raise ProjectImportError(
                ("Failed to get code from '%s' (hg update): %s"
                 % (self.repo_url, pull_output[0]))
            )
        return update_output

    def clone(self):
        self.make_clean_working_dir()
        output = self.run('hg', 'clone', self.repo_url, '.')
        if output[0] != 0:
            raise ProjectImportError(
                ("Failed to get code from '%s' (hg clone): %s"
                 % (self.repo_url, output[0]))
            )
        return output

    @property
    def branches(self):
        retcode, stdout = self.run('hg', 'branches', '-q')[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_branches(stdout)

    def parse_branches(self, data):
        """
        stable
        default
        """

        names = [name.lstrip() for name in data.splitlines()]
        return [VCSVersion(self, name, name) for name in names if name]

    @property
    def tags(self):
        retcode, stdout = self.run('hg', 'tags')[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self.parse_tags(stdout)

    def parse_tags(self, data):
        """
        Parses output of `hg tags`, eg:

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
            revision, commit_hash = commit.split(':')
            vcs_tags.append(VCSVersion(self, commit_hash, name))
        return vcs_tags

    @property
    def commit(self):
        retcode, stdout = self.run('hg', 'id', '-i')[:2]
        return stdout.strip()

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        if not identifier:
            identifier = 'tip'
        retcode = self.run('hg', 'status')[0]
        if retcode == 0:
            self.run('hg', 'pull')
            return self.run('hg', 'update', '-C', identifier)
        else:
            self.clone()
            return self.run('hg', 'update', '-C', identifier)
