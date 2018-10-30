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
from readthedocs.projects.models import Feature

log = logging.getLogger(__name__)


def get_absolute_static_url():
    """
    Get the fully qualified static URL from settings.

    Mkdocs needs a full domain because it tries to link to local files.
    """
    static_url = settings.STATIC_URL

    if not static_url.startswith('http'):
        domain = getattr(settings, 'PRODUCTION_DOMAIN')
        static_url = 'http://{}{}'.format(domain, static_url)

    return static_url


class BaseMkdocs(BaseBuilder):

    """Mkdocs builder."""

    # The default theme for mkdocs is the 'mkdocs' theme
    DEFAULT_THEME_NAME = 'mkdocs'

    def __init__(self, *args, **kwargs):
        super(BaseMkdocs, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(
            self.version.project.checkout_path(self.version.slug),
            self.build_dir)
        self.root_path = self.version.project.checkout_path(self.version.slug)
        self.yaml_file = self.get_yaml_config()

        # README: historically, the default theme was ``readthedocs`` but in
        # https://github.com/rtfd/readthedocs.org/pull/4556 we change it to
        # ``mkdocs`` to maintain the same behavior in Read the Docs than
        # building locally. Although, we can't apply this into the Corporate
        # site. To keep the same default theme there, we created a Feature flag
        # for these project that were building with MkDocs in the Corporate
        # site.
        if self.project.has_feature(Feature.MKDOCS_THEME_RTD):
            self.DEFAULT_THEME_NAME = 'readthedocs'
            log.warning(
                'Project using readthedocs theme as default for MkDocs: slug=%s',
                self.project.slug,
            )
        else:
            self.DEFAULT_THEME_NAME = 'mkdocs'


    def get_yaml_config(self):
        """Find the ``mkdocs.yml`` file in the project root."""
        mkdoc_path = self.config.mkdocs.configuration
        if not mkdoc_path:
            mkdoc_path = os.path.join(
                self.project.checkout_path(self.version.slug),
                'mkdocs.yml'
            )
            if not os.path.exists(mkdoc_path):
                return None
        return mkdoc_path

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
        static_url = get_absolute_static_url()
        user_config.setdefault('extra_javascript', []).extend([
            'readthedocs-data.js',
            '%score/js/readthedocs-doc-embed.js' % static_url,
            '%sjavascript/readthedocs-analytics.js' % static_url,
        ])
        user_config.setdefault('extra_css', []).extend([
            '%scss/badge_only.css' % static_url,
            '%scss/readthedocs-doc-embed.css' % static_url,
        ])

        # The docs path is relative to the location
        # of the mkdocs configuration file.
        docs_path = os.path.join(
            os.path.dirname(self.yaml_file),
            docs_dir
        )

        # RTD javascript writing
        rtd_data = self.generate_rtd_data(
            docs_dir=os.path.relpath(docs_path, self.root_path),
            mkdocs_config=user_config
        )
        with open(os.path.join(docs_path, 'readthedocs-data.js'), 'w') as f:
            f.write(rtd_data)

        # Use Read the Docs' analytics setup rather than mkdocs'
        # This supports using RTD's privacy improvements around analytics
        user_config['google_analytics'] = None

        # README: make MkDocs to use ``readthedocs`` theme as default if the
        # user didn't specify a specific theme manually
        if self.project.has_feature(Feature.MKDOCS_THEME_RTD):
            if 'theme' not in user_config:
                # mkdocs<0.17 syntax
                user_config['theme'] = self.DEFAULT_THEME_NAME

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
            'ad_free': not self.project.show_advertising,
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
        if self.config.mkdocs.fail_on_warning:
            build_command.append('--strict')
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
            return theme_setting.get('name') or self.DEFAULT_THEME_NAME

        if theme_setting:
            # A string which is the name of the theme
            return theme_setting

        theme_dir = mkdocs_config.get('theme_dir')
        if theme_dir:
            # Use the name of the directory in this project's custom theme directory
            return theme_dir.rstrip('/').split('/')[-1]

        return self.DEFAULT_THEME_NAME


class MkdocsHTML(BaseMkdocs):
    type = 'mkdocs'
    builder = 'build'
    build_dir = '_build/html'


class MkdocsJSON(BaseMkdocs):
    type = 'mkdocs_json'
    builder = 'json'
    build_dir = '_build/json'
