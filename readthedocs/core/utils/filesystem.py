"""
File system utilities.

Provides wrappers around common path operations
with some security checks in place.
"""

import shutil
from pathlib import Path

import structlog
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation

from readthedocs.doc_builder.exceptions import (
    FileIsNotRegularFile,
    SymlinkOutsideBasePath,
    UnsupportedSymlinkFileError,
)

log = structlog.get_logger(__name__)


def _assert_path_is_inside_docroot(path):
    resolved_path = path.absolute().resolve()
    docroot = Path(settings.DOCROOT).absolute()
    if not path.is_relative_to(docroot):
        log.error(
            "Suspicious operation outside the docroot directory.",
            path_resolved=str(resolved_path),
        )
        raise SuspiciousFileOperation(path)


def safe_open(path, *args, allow_symlinks=False, base_path=None, **kwargs):
    """
    Wrapper around path.open() to check for symlinks.

    - Checks for symlinks to avoid symlink following vulnerabilities
       like GHSA-368m-86q9-m99w.
    - Checks that files aren't out of the DOCROOT directory.

    :param allow_symlinks: If `False` and the path is a symlink, raise `FileIsSymlink`
     This prevents reading the contents of other files users shouldn't have access to.

    :param base_path: If given, check that the path isn't located outside the base path
     (usually the directory where the project was cloned).
     It must be given if `allow_symlinks` is set to `True`.
     This prevents path traversal attacks (even when using symlinks).

    The extra *args and **kwargs will be passed to the open() method.

    .. warning::

       This operation isn't safe to TocTou (Time-of-check to Time-of-use) attacks.
       Users shouldn't be able to change files while this operation is done.
    """
    if allow_symlinks and not base_path:
        raise ValueError("base_path mut be given if symlinks are allowed.")

    path = Path(path).absolute()

    log.bind(
        path_resolved=str(path.absolute().resolve()),
    )

    if path.exists() and not path.is_file():
        raise FileIsNotRegularFile(path)

    if not allow_symlinks and path.is_symlink():
        log.info("Skipping file becuase it's a symlink.")
        raise UnsupportedSymlinkFileError(path)

    # Expand symlinks.
    resolved_path = path.resolve()

    if allow_symlinks and base_path:
        base_path = Path(base_path).absolute()
        if not resolved_path.is_relative_to(base_path):
            # Trying to path traversal via a symlink, sneaky!
            log.info("Path traversal via symlink.")
            raise SymlinkOutsideBasePath(path)

    _assert_path_is_inside_docroot(resolved_path)

    return resolved_path.open(*args, **kwargs)


def safe_copytree(from_dir, to_dir, *args, **kwargs):
    """
    Wrapper around shutil.copytree to check for symlinks.

    If any of the directories point to symlinks, cancel the operation.
    We don't want to copy contents outside of those directories.

    The extra *args and **kwargs will be passed to the copytree() function.

    .. warning::

       This operation isn't safe to TocTou (Time-of-check to Time-of-use) attacks.
       Users shouldn't be able to change files while this operation is done.
    """
    from_dir = Path(from_dir)
    to_dir = Path(to_dir)
    if from_dir.is_symlink() or to_dir.is_symlink():
        log.info(
            "Not copying directory, one of the paths is a symlink.",
            from_dir=from_dir,
            from_dir_resolved=from_dir.resolve(),
            to_dir=to_dir,
            to_dir_resolved=to_dir.resolve(),
        )
        return False

    _assert_path_is_inside_docroot(from_dir)
    _assert_path_is_inside_docroot(to_dir)

    return shutil.copytree(
        from_dir,
        to_dir,
        *args,
        # Copy symlinks as is, instead of its contents.
        symlinks=True,
        **kwargs,
    )


def safe_rmtree(path, *args, **kwargs):
    """
    Wrapper around shutil.rmtree to check for symlinks.

    shutil.rmtree doens't follow symlinks by default,
    this function just logs in case users are trying to use symlinks.
    https://docs.python.org/3/library/shutil.html#shutil.rmtree

    The extra *args and **kwargs will be passed to the rmtree() function.
    """
    path = Path(path)
    if path.is_symlink():
        log.info(
            "Not deleting directory because it's a symlink.",
            path=str(path),
            resolved_path=path.resolve(),
        )
        return None
    _assert_path_is_inside_docroot(path)
    return shutil.rmtree(path, *args, **kwargs)
