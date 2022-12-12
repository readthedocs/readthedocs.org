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


def safe_open(path, *args, base_path=None, **kwargs):
    """
    Wrapper around path.open() to check for symlinks.

    - Checks for symlinks to avoid symlink following vulnerabilities
       like GHSA-368m-86q9-m99w.
    - Checks that files aren't out of the DOCROOT directory.

    :param base_path: If given, check that the path isn't located outside the base path
     (usually the directory where the project was cloned).

    The extra *args and **kwargs will be passed to the open() method.

    .. warning::

       This operation isn't safe to TocTou (Time-of-check to Time-of-use) attacks.
       Users shouldn't be able to change files while this operation is done.
    """

    docroot = Path(settings.DOCROOT).absolute()
    path = Path(path).absolute()

    # TODO: this `relative_path` can be improved to remove the first part:
    # /symlink-security-exploit/artifacts/latest/generic/passwd.txt
    # This is shown to the user currently.
    relative_path = str(path).replace(str(docroot.resolve()), '')
    log.bind(
        relative_path=relative_path,
    )

    if path.is_symlink():
        symlink_path = str(path.readlink().resolve())
        log.bind(
            symlink_path=symlink_path,
        )

    if path.exists() and not path.is_file():
        raise FileIsNotRegularFile(path)

    # Expand symlinks
    resolved_path = path.resolve()

    # Don't follow symlinks outside DOCROOT or base_path
    if path.is_symlink() and (not resolved_path.is_relative_to(docroot) or (base_path and not resolved_path.is_relative_to(base_path))):
            raise UnsupportedSymlinkFileError(filepath=relative_path)

    return resolved_path.open(*args, **kwargs)


# NOTE: I think `safe_copytree` is useful with `symlinks=True`,
# and we shouldn't perform all the other checks here.
# We are always using `safe_open` at the storage level,
# and we can keep all these checks contained there (in one place)
def safe_copytree(from_dir, to_dir, *args, **kwargs):
    """
    Wrapper around shutil.copytree to copy symlinks as is, instead of its contents.

    The extra *args and **kwargs will be passed to the copytree() function.

    .. warning::

       This operation isn't safe to TocTou (Time-of-check to Time-of-use) attacks.
       Users shouldn't be able to change files while this operation is done.
    """
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
    Wrapper around shutil.rmtree for security reasons.

    shutil.rmtree doens't follow symlinks by default,
    https://docs.python.org/3/library/shutil.html#shutil.rmtree

    The extra *args and **kwargs will be passed to the rmtree() function.
    """
    return shutil.rmtree(path, *args, **kwargs)
