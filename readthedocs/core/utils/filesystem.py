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

from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.doc_builder.exceptions import FileIsNotRegularFile
from readthedocs.doc_builder.exceptions import SymlinkOutsideBasePath
from readthedocs.doc_builder.exceptions import UnsupportedSymlinkFileError


log = structlog.get_logger(__name__)

MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024 * 1  # 1 GB


def assert_path_is_inside_docroot(path):
    """
    Assert that the given path is inside the DOCROOT directory.

    Symlinks are resolved before checking, a SuspiciousFileOperation exception
    will be raised if the path is outside the DOCROOT.

    .. warning::

       This operation isn't safe to TocTou (Time-of-check to Time-of-use) attacks.
       Users shouldn't be able to change files while this operation is done.
    """
    resolved_path = path.absolute().resolve()
    docroot = Path(settings.DOCROOT).absolute()
    if not path.is_relative_to(docroot):
        log.error(
            "Suspicious operation outside the docroot directory.",
            path_resolved=str(resolved_path),
            docroot=settings.DOCROOT,
        )
        raise SuspiciousFileOperation(path)


def safe_open(
    path, *args, allow_symlinks=False, base_path=None, max_size_bytes=MAX_FILE_SIZE_BYTES, **kwargs
):
    """
    Wrapper around path.open() to check for symlinks.

    - Checks for symlinks to avoid symlink following vulnerabilities
       like GHSA-368m-86q9-m99w.
    - Checks that files aren't out of the DOCROOT directory.
    - Checks that files aren't too large.

    :param allow_symlinks: If `False` and the path is a symlink, raise `FileIsSymlink`
     This prevents reading the contents of other files users shouldn't have access to.

    :param base_path: If given, check that the path isn't located outside the base path
     (usually the directory where the project was cloned).
     It must be given if `allow_symlinks` is set to `True`.
     This prevents path traversal attacks (even when using symlinks).
    :param max_size_bytes: Maximum file size allowed in bytes when reading a file.

    The extra *args and **kwargs will be passed to the open() method.

    .. warning::

       This operation isn't safe to TocTou (Time-of-check to Time-of-use) attacks.
       Users shouldn't be able to change files while this operation is done.
    """
    if allow_symlinks and not base_path:
        raise ValueError("base_path must be given if symlinks are allowed.")

    path = Path(path).absolute()

    structlog.contextvars.bind_contextvars(
        path_resolved=str(path.absolute().resolve()),
    )

    if path.exists() and not path.is_file():
        raise FileIsNotRegularFile(FileIsNotRegularFile.SYMLINK_USED)

    if not allow_symlinks and path.is_symlink():
        log.info("Skipping file because it's a symlink.")
        raise UnsupportedSymlinkFileError(UnsupportedSymlinkFileError.SYMLINK_USED)

    # Expand symlinks.
    resolved_path = path.resolve()

    if resolved_path.exists():
        file_size = resolved_path.stat().st_size
        if file_size > max_size_bytes:
            log.info("File is too large.", size_bytes=file_size)
            raise BuildUserError(BuildUserError.FILE_TOO_LARGE)

    if allow_symlinks and base_path:
        base_path = Path(base_path).absolute()
        if not resolved_path.is_relative_to(base_path):
            # Trying to path traversal via a symlink, sneaky!
            log.info("Path traversal via symlink.")
            raise SymlinkOutsideBasePath(SymlinkOutsideBasePath.SYMLINK_USED)

    assert_path_is_inside_docroot(resolved_path)

    # The encoding is valid only if the file opened is a text file,
    # this function is used to read both types of files (text and binary),
    # so we can't specify the encoding here.
    # pylint: disable=unspecified-encoding
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

    assert_path_is_inside_docroot(from_dir)
    assert_path_is_inside_docroot(to_dir)

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
    assert_path_is_inside_docroot(path)
    return shutil.rmtree(path, *args, **kwargs)
