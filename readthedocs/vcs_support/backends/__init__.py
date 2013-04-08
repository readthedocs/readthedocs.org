from . import bzr, hg, git, svn

backend_cls = {
    'bzr': bzr.Backend,
    'launchpad': bzr.Backend,
    'svn': svn.Backend,
    'git': git.Backend,
    'hg': hg.Backend,
}
