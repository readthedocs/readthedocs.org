"""
MkDocs_ backend for building docs.

.. _MkDocs: http://www.mkdocs.org/
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import json
import logging
import os

import yaml
from django.conf import settings
from django.template import loader as template_loader

from readthedocs.doc_builder.base import BaseBuilder
from readthedocs.doc_builder.exceptions import BuildEnvironmentError

log = logging.getLogger(__name__)


def get_absolute_media_url():
    """
    Get the fully qualified media URL from settings.

    Mkdocs needs a full domain because it tries to link to local media files.
    """
    media_url = settings.MEDIA_URL

    if not media_url.startswith('http'):
        domain = getattr(settings, 'PRODUCTION_DOMAIN')
        media_url = 'http://{}{}'.format(domain, media_url)

    return media_url


class BaseMkdocs(BaseBuilder):

    """Mkdocs builder."""

    use_theme = True

    # The default theme for mkdocs (outside of RTD) is the 'mkdocs' theme
    # For RTD, our default is the 'readthedocs' theme
    READTHEDOCS_THEME_NAME = 'readthedocs'

    # Overrides for the 'readthedocs' theme that include
    # search utilities and version selector
    READTHEDOCS_TEMPLATE_OVERRIDE_DIR = (
        '%s/readthedocs/templates/mkdocs/readthedocs' % settings.SITE_ROOT
    )

    def __init__(self, *args, **kwargs):
        super(BaseMkdocs, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(
            self.version.project.checkout_path(self.version.slug),
            self.build_dir)
        self.root_path = self.version.project.checkout_path(self.version.slug)
        self.yaml_file = self.get_yaml_config()

    def get_yaml_config(self):
        """Find the ``mkdocs.yml`` file in the project root."""
        # TODO: try to load from the configuration file first.
        test_path = os.path.join(
            self.project.checkout_path(self.version.slug),
            'mkdocs.yml'
        )
        if os.path.exists(test_path):
            return test_path
        return None

    def load_yaml_config(self):
        """
        Load a YAML config.

        Raise BuildEnvironmentError if failed due to syntax errors.
        """
        try:
            return yaml.safe_load(
                open(self.yaml_file, 'r')
            )
        except IOError:
            return {
                'site_name': self.version.project.name,
            }
        except yaml.YAMLError as exc:
            note = ''
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                note = ' (line %d, column %d)' % (mark.line + 1, mark.column + 1)
            raise BuildEnvironmentError(
                'Your mkdocs.yml could not be loaded, '
                'possibly due to a syntax error{note}'.format(note=note)
            )

    def append_conf(self, **__):
        """Set mkdocs config values."""
        if not self.yaml_file:
            self.yaml_file = os.path.join(self.root_path, 'mkdocs.yml')

        user_config = self.load_yaml_config()

        # Handle custom docs dirs
        user_docs_dir = user_config.get('docs_dir')
        docs_dir = self.docs_dir(docs_dir=user_docs_dir)
        self.create_index(extension='md')
        user_config['docs_dir'] = docs_dir

        # Set mkdocs config values
        media_url = get_absolute_media_url()
        user_config.setdefault('extra_javascript', []).extend([
            'readthedocs-data.js',
            '%sstatic/core/js/readthedocs-doc-embed.js' % media_url,
            '%sjavascript/readthedocs-analytics.js' % media_url,
        ])
        user_config.setdefault('extra_css', []).extend([
            '%scss/badge_only.css' % media_url,
            '%scss/readthedocs-doc-embed.css' % media_url,
        ])

        docs_path = os.path.join(self.root_path, docs_dir)

        # RTD javascript writing
        rtd_data = self.generate_rtd_data(
            docs_dir=docs_dir,
            mkdocs_config=user_config
        )
        with open(os.path.join(docs_path, 'readthedocs-data.js'), 'w') as f:
            f.write(rtd_data)

        # Use Read the Docs' analytics setup rather than mkdocs'
        # This supports using RTD's privacy improvements around analytics
        user_config['google_analytics'] = None

        # If using the readthedocs theme, apply the readthedocs.org overrides
        # These use a global readthedocs search
        # and customize the version selector.
        self.apply_theme_override(user_config)

        # Write the modified mkdocs configuration
        yaml.safe_dump(
            user_config,
            open(self.yaml_file, 'w')
        )

        # Write the mkdocs.yml to the build logs
        self.run(
            'cat',
            os.path.relpath(self.yaml_file, self.root_path),
            cwd=self.root_path,
        )

    def generate_rtd_data(self, docs_dir, mkdocs_config):
        """Generate template properties and render readthedocs-data.js."""
        # Use the analytics code from mkdocs.yml
        # if it isn't set already by Read the Docs,
        analytics_code = self.version.project.analytics_code
        if not analytics_code and mkdocs_config.get('google_analytics'):
            # http://www.mkdocs.org/user-guide/configuration/#google_analytics
            analytics_code = mkdocs_config['google_analytics'][0]

        # Will be available in the JavaScript as READTHEDOCS_DATA.
        readthedocs_data = {
            'project': self.version.project.slug,
            'version': self.version.slug,
            'language': self.version.project.language,
            'programming_language': self.version.project.programming_language,
            'page': None,
            'theme': self.get_theme_name(mkdocs_config),
            'builder': "mkdocs",
            'docroot': docs_dir,
            'source_suffix': ".md",
            'api_host': getattr(settings, 'PUBLIC_API_URL', 'https://readthedocs.org'),
            'commit': self.version.project.vcs_repo(self.version.slug).commit,
            'global_analytics_code': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
            'user_analytics_code': analytics_code,
        }
        data_json = json.dumps(readthedocs_data, indent=4)
        data_ctx = {
            'data_json': data_json,
            'current_version': readthedocs_data['version'],
            'slug': readthedocs_data['project'],
            'html_theme': readthedocs_data['theme'],
            'pagename': None,
        }
        tmpl = template_loader.get_template('doc_builder/data.js.tmpl')
        return tmpl.render(data_ctx)

    def build(self):
        checkout_path = self.project.checkout_path(self.version.slug)
        build_command = [
            'python',
            self.python_env.venv_bin(filename='mkdocs'),
            self.builder,
            '--clean',
            '--site-dir', self.build_dir,
            '--config-file', self.yaml_file,
        ]
        if self.use_theme:
            build_command.extend(['--theme', 'readthedocs'])
        cmd_ret = self.run(
            *build_command,
            cwd=checkout_path,
            bin_path=self.python_env.venv_bin()
        )
        return cmd_ret.successful

    def get_theme_name(self, mkdocs_config):
        """
        Get the theme configuration in the mkdocs_config

        In v0.17.0, the theme configuration switched
        from two separate configs (both optional) to a nested directive.

        :see: http://www.mkdocs.org/about/release-notes/#theme-customization-1164
        :returns: the name of the theme RTD will use
        """
        theme_setting = mkdocs_config.get('theme')
        if isinstance(theme_setting, dict):
            # Full nested theme config (the new configuration)
            return theme_setting.get('name') or self.READTHEDOCS_THEME_NAME

        if theme_setting:
            # A string which is the name of the theme
            return theme_setting

        theme_dir = mkdocs_config.get('theme_dir')
        if theme_dir:
            # Use the name of the directory in this project's custom theme directory
            return theme_dir.rstrip('/').split('/')[-1]

        return self.READTHEDOCS_THEME_NAME

    def apply_theme_override(self, mkdocs_config):
        """
        Apply theme overrides for the RTD theme (modifies the ``mkdocs_config`` parameter)

        In v0.17.0, the theme configuration switched
        from two separate configs (both optional) to a nested directive.
        How to override the theme depends on whether the new or old configuration
        is used.

        :see: http://www.mkdocs.org/about/release-notes/#theme-customization-1164
        """
        if self.get_theme_name(mkdocs_config) == self.READTHEDOCS_THEME_NAME:
            # Overriding the theme is only necessary
            # if the 'readthedocs' theme is used.
            theme_setting = mkdocs_config.get('theme')
            if isinstance(theme_setting, dict):
                theme_setting['custom_dir'] = self.READTHEDOCS_TEMPLATE_OVERRIDE_DIR
            else:
                mkdocs_config['theme_dir'] = self.READTHEDOCS_TEMPLATE_OVERRIDE_DIR


class MkdocsHTML(BaseMkdocs):
    type = 'mkdocs'
    builder = 'build'
    build_dir = '_build/html'


class MkdocsJSON(BaseMkdocs):
    type = 'mkdocs_json'
    builder = 'json'
    build_dir = '_build/json'
    use_theme = False
