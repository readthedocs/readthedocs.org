from projects.exceptions import ProjectImportError
from launchpadlib.launchpad import Launchpad
from vcs_support.base import VCSVersion
from vcs_support.backends import bzr


class Backend(bzr.Backend):
    supports_branches = True
    _launchpad = None
    _lp_project = None

    def get_branches(self):
        branches = []
        proj = self._get_project()

        for series in proj.series:
            branches.append( VCSVersion(self, series.branch.bzr_identity, series.name) )

        return branches

    def _get_project(self):
        if self._lp_project is None:
            lp = self._get_launchpad()
            self._lp_project = lp.projects[self.project.slug] # Probably need to improve this
        return self._lp_project

    def _get_launchpad(self):
        if self._launchpad is None:
            client_id = 'rtfd-client-%s' % self.project.name
            self._launchpad = Launchpad.login_anonymously(client_id, 'production')
        return self._launchpad
