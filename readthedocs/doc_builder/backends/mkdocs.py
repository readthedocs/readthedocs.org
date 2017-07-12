"""MkDocs_ backend for building docs.

.. _MkDocs: http://www.mkdocs.org/

"""
from __future__ import absolute_import
import os
import logging
import json
import yaml

from django.conf import settings
from django.template import loader as template_loader

from readthedocs.doc_builder.base import BaseBuilder
from readthedocs.doc_builder.exceptions import BuildEnvironmentError

log = logging.getLogger(__name__)

TEMPLATE_DIR = '%s/readthedocs/templates/mkdocs/readthedocs' % settings.SITE_ROOT
OVERRIDE_TEMPLATE_DIR = '%s/readthedocs/templates/mkdocs/overrides' % settings.SITE_ROOT


def get_absolute_media_url():
    """Get the fully qualified media URL from settings.

    Mkdocs needs a full domain because it tries to link to local media files.

    """
    media_url = settings.MEDIA_URL

    if not media_url.startswith('http'):
        domain = getattr(settings, 'PRODUCTION_DOMAIN')
        media_url = 'http://{}{}'.format(domain, media_url)

    return media_url


class BaseMkdocs(BaseBuilder):

    """Mkdocs builder"""

    use_theme = True

    def __init__(self, *args, **kwargs):
        super(BaseMkdocs, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(
            self.version.project.checkout_path(self.version.slug),
            self.build_dir)
        self.root_path = self.version.project.checkout_path(self.version.slug)

    def load_yaml_config(self):
        """Load a YAML config.

        Raise BuildEnvironmentError if failed due to syntax errors.

        """
        try:
            return yaml.safe_load(
                open(os.path.join(self.root_path, 'mkdocs.yml'), 'r')
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
                "Your mkdocs.yml could not be loaded, "
                "possibly due to a syntax error%s" % (
                    note,))

    def append_conf(self, **__):
        """Set mkdocs config values"""
        # Pull mkdocs config data
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
            'readthedocs-dynamic-include.js',
            '%sstatic/core/js/readthedocs-doc-embed.js' % media_url
        ])
        user_config.setdefault('extra_css', []).extend([
            '%scss/badge_only.css' % media_url,
            '%scss/readthedocs-doc-embed.css' % media_url,
        ])

        # Set our custom theme dir for mkdocs
        if 'theme_dir' not in user_config and self.use_theme:
            user_config['theme_dir'] = TEMPLATE_DIR

        yaml.safe_dump(
            user_config,
            open(os.path.join(self.root_path, 'mkdocs.yml'), 'w')
        )

        docs_path = os.path.join(self.root_path, docs_dir)

        # RTD javascript writing
        rtd_data = self.generate_rtd_data(docs_dir=docs_dir)
        with open(os.path.join(docs_path, 'readthedocs-data.js'), 'w') as f:
            f.write(rtd_data)

        dynamic_include = self.generate_dynamic_include()
        with open(os.path.join(docs_path, 'readthedocs-dynamic-include.js'), 'w') as f:
            f.write(dynamic_include)

    def generate_rtd_data(self, docs_dir):
        """Generate template properties and render readthedocs-data.js."""
        # Will be available in the JavaScript as READTHEDOCS_DATA.
        readthedocs_data = {
            'project': self.version.project.slug,
            'version': self.version.slug,
            'language': self.version.project.language,
            'page': None,
            'theme': "readthedocs",
            'builder': "mkdocs",
            'docroot': docs_dir,
            'source_suffix': ".md",
            'api_host': getattr(settings, 'PUBLIC_API_URL', 'https://readthedocs.org'),
            'commit': self.version.project.vcs_repo(self.version.slug).commit,
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

    def generate_dynamic_include(self):
        include_ctx = {
            'global_analytics_code': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
            'user_analytics_code': self.version.project.analytics_code,
        }
        tmpl = template_loader.get_template('doc_builder/include.js.tmpl')
        return tmpl.render(include_ctx)

    def build(self):
        checkout_path = self.project.checkout_path(self.version.slug)
        build_command = [
            'python',
            self.python_env.venv_bin(filename='mkdocs'),
            self.builder,
            '--clean',
            '--site-dir', self.build_dir,
        ]
        if self.use_theme:
            build_command.extend(['--theme', 'readthedocs'])
        cmd_ret = self.run(
            *build_command,
            cwd=checkout_path,
            bin_path=self.python_env.venv_bin()
        )
        return cmd_ret.successful


class MkdocsHTML(BaseMkdocs):
    type = 'mkdocs'
    builder = 'build'
    build_dir = '_build/html'


class MkdocsJSON(BaseMkdocs):
    type = 'mkdocs_json'
    builder = 'json'
    build_dir = '_build/json'
    use_theme = False

    def build(self):
        user_config = yaml.safe_load(
            open(os.path.join(self.root_path, 'mkdocs.yml'), 'r')
        )
        if user_config['theme_dir'] == TEMPLATE_DIR:
            del user_config['theme_dir']
        yaml.safe_dump(
            user_config,
            open(os.path.join(self.root_path, 'mkdocs.yml'), 'w')
        )
        super(MkdocsJSON, self).build()
