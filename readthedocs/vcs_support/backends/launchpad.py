from launchpadlib.launchpad import Launchpad
from vcs_support.base import VCSVersion
from vcs_support.backends import bzr


class Backend(bzr.Backend):
    supports_branches = True
    launchpad = None
    lp_project = None

    @property
    def branches(self):
        branches = []
        proj = self.get_project()

        for series in proj.series:
            branches.append(
                VCSVersion(self, series.branch.bzr_identity, series.name))

        return branches

    def get_project(self):
        if self.lp_project is None:
            lp = self.get_launchpad()
            self.lp_project = lp.projects[self.slug] # Probably need to improve this
        return self.lp_project

    def get_launchpad(self):
        if self.launchpad is None:
            client_id = 'rtfd-client-%s' % self.repo.name
            self.launchpad = Launchpad.login_anonymously(
                client_id, 'production')
        return self.launchpad
