"""Listing of all the VCS backends."""
from . import bzr, git, hg, svn

backend_cls = {
    "bzr": bzr.Backend,
    "svn": svn.Backend,
    "git": git.Backend,
    "hg": hg.Backend,
}
