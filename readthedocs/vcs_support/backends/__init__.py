"""Listing of all the VCS backends."""
from __future__ import absolute_import
from . import bzr, hg, git, svn

backend_cls = {
    'bzr': bzr.Backend,
    'svn': svn.Backend,
    'git': git.Backend,
    'hg': hg.Backend,
}
