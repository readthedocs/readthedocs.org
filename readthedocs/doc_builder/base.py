# -*- coding: utf-8 -*-
"""Base classes for Builders."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging
import os
import shutil
import textwrap
from functools import wraps

from builtins import open

log = logging.getLogger(__name__)


def restoring_chdir(fn):
    # XXX:dc: This would be better off in a neutral module
    @wraps(fn)
    def decorator(*args, **kw):
        try:
            path = os.getcwd()
            return fn(*args, **kw)
        finally:
            os.chdir(path)

    return decorator


class BaseBuilder(object):

    """
    The Base for all Builders. Defines the API for subclasses.

    Expects subclasses to define ``old_artifact_path``, which points at the
    directory where artifacts should be copied from.
    """

    _force = False

    ignore_patterns = []

    # old_artifact_path = ..

    def __init__(self, build_env, python_env, force=False):
        self.build_env = build_env
        self.python_env = python_env
        self.version = build_env.version
        self.project = build_env.project
        self.config = python_env.config if python_env else None
        self._force = force
        self.target = self.project.artifact_path(
            version=self.version.slug, type_=self.type)

    def force(self, **__):
        """An optional step to force a build even when nothing has changed."""
        log.info('Forcing a build')
        self._force = True

    def build(self):
        """Do the actual building of the documentation."""
        raise NotImplementedError

    def move(self, **__):
        """Move the generated documentation to its artifact directory."""
        if os.path.exists(self.old_artifact_path):
            if os.path.exists(self.target):
                shutil.rmtree(self.target)
            log.info('Copying %s on the local filesystem', self.type)
            log.info('Ignoring patterns %s', self.ignore_patterns)
            shutil.copytree(
                self.old_artifact_path,
                self.target,
                ignore=shutil.ignore_patterns(*self.ignore_patterns)
            )
        else:
            log.warning('Not moving docs, because the build dir is unknown.')

    def clean(self, **__):
        """Clean the path where documentation will be built."""
        if os.path.exists(self.old_artifact_path):
            shutil.rmtree(self.old_artifact_path)
            log.info('Removing old artifact path: %s', self.old_artifact_path)

    def docs_dir(self, docs_dir=None, **__):
        """Handle creating a custom docs_dir if it doesn't exist."""
        checkout_path = self.project.checkout_path(self.version.slug)
        if not docs_dir:
            for doc_dir_name in ['docs', 'doc', 'Doc', 'book']:
                possible_path = os.path.join(checkout_path, doc_dir_name)
                if os.path.exists(possible_path):
                    docs_dir = possible_path
                    break
        if not docs_dir:
            docs_dir = checkout_path
        return docs_dir

    def create_index(self, extension='md', force_index=False, **__):
        """
        Create an index file if it needs it.

        If force_index is True and there isn't an index file,
        one is created whether or not there is a README file.
        """
        docs_dir = self.docs_dir()

        index_filename = os.path.join(
            docs_dir, 'index.{ext}'.format(ext=extension)
        )
        readme_filename = os.path.join(
            docs_dir, 'README.{ext}'.format(ext=extension)
        )
        if os.path.exists(index_filename):
            return 'index'
        if not force_index and os.path.exists(readme_filename):
            return 'README'

        index_text = textwrap.dedent(
            """
            Welcome to Read the Docs
            ------------------------

            This is an autogenerated index file.

            Please create an ``index.{ext}`` or ``README.{ext}`` (Sphinx only) file with
            your own content under the root (or ``/docs``) directory in your repository.

            If you want to use another markup, choose a different builder in your settings.
            Check out our `Getting Started Guide
            <https://docs.readthedocs.io/en/latest/getting_started.html>`_ to become more
            familiar with Read the Docs.
            """
        )
        with open(index_filename, 'w+') as index_file:
            index_file.write(
                index_text.format(dir=docs_dir, ext=extension)
            )
        return 'index'

    def run(self, *args, **kwargs):
        """Proxy run to build environment."""
        return self.build_env.run(*args, **kwargs)
