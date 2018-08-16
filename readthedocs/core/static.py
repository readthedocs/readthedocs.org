# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from django.contrib.staticfiles.finders import FileSystemFinder


class SelectiveFileSystemFinder(FileSystemFinder):

    """
    Add user media paths in ``media/`` to ignore patterns.

    This allows collectstatic inside ``media/`` without collecting all of the
    paths that include user files
    """

    def list(self, ignore_patterns):
        ignore_patterns.extend(['epub', 'pdf', 'htmlzip', 'json', 'man'])
        return super(SelectiveFileSystemFinder, self).list(ignore_patterns)
