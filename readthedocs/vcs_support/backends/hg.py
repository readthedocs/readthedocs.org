from projects.exceptions import ProjectImportError
from vcs_support.base import BaseVCS, VCSVersion


class Backend(BaseVCS):
    supports_tags = True
    fallback_branch = 'default'

    def update(self):
        super(Backend, self).update()
        retcode = self._run_command('hg', 'status')[0]
        if retcode == 0:
            self._pull()
        else:
            self._clone()

    def _pull(self):
        retcode = self._run_command('hg', 'pull')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (hg pull): %s" % (self.repo_url, retcode)
            )
        retcode = self._run_command('hg', 'update', '-C')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (hg update): %s" % (self.repo_url, retcode)
            )

    def _clone(self):
        retcode = self._run_command('hg', 'clone', self.repo_url, '.')[0]
        if retcode != 0:
            raise ProjectImportError(
                "Failed to get code from '%s' (hg clone): %s" % (self.repo_url, retcode)
            )

    def get_tags(self):
        retcode, stdout = self._run_command('hg', 'tags')[:2]
        # error (or no tags found)
        if retcode != 0:
            return []
        return self._parse_tags(stdout)

    def _parse_tags(self, data):
        """
        Parses output of show-ref --tags, eg:

        tip                              278:c4b2d21db51a
        0.2.2                            152:6b0364d98837
        0.2.1                            117:a14b7b6ffa03
        0.1                               50:30c2c6b3a055
        """
        # parse the lines into a list of tuples (commit-hash, tag ref name)
        raw_tags = [line.rsplit(' ', 1) for line in data.strip('\n').split('\n')]
        vcs_tags = []
        for name, commit in raw_tags:
            clean_name = name.strip(' ')
            if clean_name == 'tip':
                continue
            commit_hash = commit.split(':')[1]
            vcs_tags.append(VCSVersion(self, commit_hash, clean_name))
        return vcs_tags

    def checkout(self, identifier=None):
        super(Backend, self).checkout()
        if not identifier:
            identifier = 'tip'
        retcode = self._run_command('hg', 'status')[0]
        if retcode == 0:
            self._run_command('hg', 'pull')
            self._run_command('hg', 'update', '-C', identifier)
        else:
            self._clone()
            self._run_command('hg', 'update', '-C', identifier)
