"""
Read the Docs custom static finders.

NOTE: I think we can probably remove it completely,
since we are not storing these files anymore inside "media/"
"""

from django.contrib.staticfiles.finders import FileSystemFinder


class SelectiveFileSystemFinder(FileSystemFinder):
    """
    Add user media paths in ``media/`` to ignore patterns.

    This allows collectstatic inside ``media/`` without collecting all of the
    paths that include user files
    """

    def list(self, ignore_patterns):
        ignore_patterns.extend(["epub", "pdf", "htmlzip", "json", "man"])
        return super().list(ignore_patterns)
