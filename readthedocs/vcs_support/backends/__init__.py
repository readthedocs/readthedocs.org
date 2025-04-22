"""Listing of all the VCS backends."""

from . import git


backend_cls = {
    "git": git.Backend,
}
