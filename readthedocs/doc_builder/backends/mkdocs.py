import os
import logging
import json
import yaml

from django.conf import settings
from django.template import Context, loader as template_loader

from readthedocs.doc_builder.base import BaseBuilder

log = logging.getLogger(__name__)

TEMPLATE_DIR = '%s/readthedocs/templates/mkdocs/readthedocs' % settings.SITE_ROOT
OVERRIDE_TEMPLATE_DIR = '%s/readthedocs/templates/mkdocs/overrides' % settings.SITE_ROOT


class BaseMkdocs(BaseBuilder):

    """
    Mkdocs builder
    """
    use_theme = True

    def __init__(self, *args, **kwargs):
        super(BaseMkdocs, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(
            self.version.project.checkout_path(self.version.slug),
            self.build_dir)
        self.root_path = self.version.project.checkout_path(self.version.slug)

    def append_conf(self, **kwargs):
        """
        Set mkdocs config values
        """

        # Pull mkdocs config data
        try:
            user_config = yaml.safe_load(
                open(os.path.join(self.root_path, 'mkdocs.yml'), 'r')
            )
        except IOError:
            user_config = {
                'site_name': self.version.project.name,
            }

        # Handle custom docs dirs

        user_docs_dir = user_config.get('docs_dir')
        if user_docs_dir:
            user_docs_dir = os.path.join(self.root_path, user_docs_dir)
        docs_dir = self.docs_dir(docs_dir=user_docs_dir)
        self.create_index(extension='md')
        user_config['docs_dir'] = docs_dir

        # Set mkdocs config values

        media_url = getattr(settings, 'MEDIA_URL', 'https://media.readthedocs.org')

        # Mkdocs needs a full domain here because it tries to link to local media files
        if not media_url.startswith('http'):
            media_url = 'http://localhost:8000' + media_url

        if 'extra_javascript' in user_config:
            user_config['extra_javascript'].append('readthedocs-data.js')
            user_config['extra_javascript'].append(
                'readthedocs-dynamic-include.js')
            user_config['extra_javascript'].append(
                '%sjavascript/readthedocs-doc-embed.js' % media_url)
        else:
            user_config['extra_javascript'] = [
                'readthedocs-data.js',
                'readthedocs-dynamic-include.js',
                '%sjavascript/readthedocs-doc-embed.js' % media_url,
            ]

        if 'extra_css' in user_config:
            user_config['extra_css'].append(
                '%s/css/badge_only.css' % media_url)
            user_config['extra_css'].append(
                '%s/css/readthedocs-doc-embed.css' % media_url)
        else:
            user_config['extra_css'] = [
                '%scss/badge_only.css' % media_url,
                '%scss/readthedocs-doc-embed.css' % media_url,
            ]

        # Set our custom theme dir for mkdocs
        if 'theme_dir' not in user_config and self.use_theme:
            user_config['theme_dir'] = TEMPLATE_DIR

        yaml.dump(
            user_config,
            open(os.path.join(self.root_path, 'mkdocs.yml'), 'w')
        )

        # RTD javascript writing

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
            'api_host': getattr(settings, 'PRODUCTION_DOMAIN', 'https://readthedocs.org'),
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
        data_string = template_loader.get_template(
            'doc_builder/data.js.tmpl'
        ).render(data_ctx)

        data_file = open(os.path.join(self.root_path, docs_dir, 'readthedocs-data.js'), 'w+')
        data_file.write(data_string)
        data_file.write('''
READTHEDOCS_DATA["page"] = mkdocs_page_input_path.substr(
    0, mkdocs_page_input_path.lastIndexOf(READTHEDOCS_DATA.source_suffix));
''')
        data_file.close()

        include_ctx = {
            'global_analytics_code': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
            'user_analytics_code': self.version.project.analytics_code,
        }
        include_string = template_loader.get_template(
            'doc_builder/include.js.tmpl'
        ).render(include_ctx)
        include_file = open(
            os.path.join(self.root_path, docs_dir, 'readthedocs-dynamic-include.js'),
            'w+'
        )
        include_file.write(include_string)
        include_file.close()

    def build(self, **kwargs):
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

    def build(self, **kwargs):
        user_config = yaml.safe_load(
            open(os.path.join(self.root_path, 'mkdocs.yml'), 'r')
        )
        if user_config['theme_dir'] == TEMPLATE_DIR:
            del user_config['theme_dir']
        yaml.dump(
            user_config,
            open(os.path.join(self.root_path, 'mkdocs.yml'), 'w')
        )
        super(MkdocsJSON, self).build(**kwargs)
