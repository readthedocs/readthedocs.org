from __future__ import absolute_import, division, print_function

from . import bzr, hg, git, svn

backend_cls = {
    'bzr': bzr.Backend,
    'svn': svn.Backend,
    'git': git.Backend,
    'hg': hg.Backend,
}
