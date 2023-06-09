"""Base classes for Builders."""

import os
from functools import wraps

import structlog

from readthedocs.core.utils.filesystem import safe_open
from readthedocs.projects.models import Feature

log = structlog.get_logger(__name__)


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


class BaseBuilder:

    """The Base for all Builders. Defines the API for subclasses."""

    ignore_patterns = []

    def __init__(self, build_env, python_env):
        self.build_env = build_env
        self.python_env = python_env
        self.version = build_env.version
        self.project = build_env.project
        self.config = python_env.config if python_env else None
        self.project_path = self.project.checkout_path(self.version.slug)
        self.api_client = self.build_env.api_client

    def get_final_doctype(self):
        """Some builders may have a different doctype at build time."""
        return self.config.doctype

    def append_conf(self):
        """Set custom configurations for this builder."""

    def build(self):
        """Do the actual building of the documentation."""
        raise NotImplementedError

    def _post_build(self):
        """Execute extra steps (e.g. create ZIP, rename PDF, etc) after building if required."""

    def docs_dir(self):
        """Handle creating a custom docs_dir if it doesn't exist."""
        for doc_dir_name in ['docs', 'doc', 'Doc', 'book']:
            possible_path = os.path.join(self.project_path, doc_dir_name)
            if os.path.exists(possible_path):
                return possible_path

        return self.project_path

    def create_index(self, extension='md', **__):
        """Create an index file if it needs it."""
        docs_dir = self.docs_dir()

        index_filename = os.path.join(
            docs_dir,
            'index.{ext}'.format(ext=extension),
        )
        if not os.path.exists(index_filename):
            readme_filename = os.path.join(
                docs_dir,
                'README.{ext}'.format(ext=extension),
            )
            if os.path.exists(readme_filename):
                return 'README'

            if not self.project.has_feature(Feature.DONT_CREATE_INDEX):
                index_text = """

Welcome to Read the Docs
------------------------

This is an autogenerated index file.

Please create an ``index.{ext}`` or ``README.{ext}`` file with your own content
under the root (or ``/docs``) directory in your repository.

If you want to use another markup, choose a different builder in your settings.
Check out our `Getting Started Guide
<https://docs.readthedocs.io/en/latest/getting_started.html>`_ to become more
familiar with Read the Docs.
                """

                with safe_open(index_filename, "w+") as index_file:
                    index_file.write(index_text.format(dir=docs_dir, ext=extension))

        return 'index'

    def run(self, *args, **kwargs):
        """Proxy run to build environment."""
        return self.build_env.run(*args, **kwargs)
