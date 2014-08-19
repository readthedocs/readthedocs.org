import codecs
import fnmatch
import os
import logging
import json
import yaml

from django.conf import settings
from django.template import Context, loader as template_loader

from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run
from projects.constants import LOG_TEMPLATE
from tastyapi import apiv2

log = logging.getLogger(__name__)


class Builder(BaseBuilder):

    """
    Mkdocs builder
    """
    type = 'mkdocs'

    def __init__(self, *args, **kwargs):
        super(Builder, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(
            self.version.project.checkout_path(self.version.slug), 'site')

    def _parse_html(self, file_path):
        """
        Prepare the text of the html file.
        """
        from pyquery import PyQuery
        try:
            with codecs.open(file_path, encoding='utf-8', mode='r') as f:
                content = f.read()
        except IOError as e:
            log.info('(Search Index) Unable to index file: %s, error :%s' % (file_path, e))
            return ''
        log.debug('(Search Index) Indexing %s' % (file_path))
        DOCUMENT_MKDOCS_PATH = getattr(settings, 'DOCUMENT_MKDOCS_PATH', 'div[role="main"]')
        try:
            to_index = PyQuery(content)(DOCUMENT_MKDOCS_PATH).text()
        except ValueError:
            #Pyquery returns ValueError if div.document doesn't exist.
            return ''
        if not to_index:
            log.info('(Search Index) Unable to index file: %s, empty file' % (file_path))
        else:
            log.debug('(Search Index) %s length: %s' % (file_path, len(to_index)))

        return to_index

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        checkout_path = project.checkout_path(self.version.slug)
        site_path = os.path.join(checkout_path, 'site')
        os.chdir(checkout_path)

        # Pull mkdocs config data
        user_config = yaml.safe_load(open('mkdocs.yml', 'r'))
        docs_dir = user_config.get('docs_dir', 'docs')

        # Set mkdocs config values

        MEDIA_URL = getattr(
            settings, 'MEDIA_URL', 'https://media.readthedocs.org')
        if 'extra_javascript' in user_config:
            user_config['extra_javascript'].append(
                '%sjavascript/jquery/jquery-2.0.3.min.js' % MEDIA_URL)
            user_config['extra_javascript'].append('readthedocs-data.js')
            user_config['extra_javascript'].append(
                'readthedocs-dynamic-include.js')
            user_config['extra_javascript'].append(
                '%sjavascript/readthedocs-doc-embed.js' % MEDIA_URL)
        else:
            user_config['extra_javascript'] = [
                '%sjavascript/jquery/jquery-2.0.3.min.js' % MEDIA_URL,
                'readthedocs-data.js',
                'readthedocs-dynamic-include.js',
                '%sjavascript/readthedocs-doc-embed.js' % MEDIA_URL,
            ]

        if 'extra_css' in user_config:
            user_config['extra_css'].append(
                'https://media.readthedocs.org/css/badge_only.css')
            user_config['extra_css'].append(
                'https://media.readthedocs.org/css/readthedocs-doc-embed.css')
        else:
            user_config['extra_css'] = [
                'https://media.readthedocs.org/css/badge_only.css',
                'https://media.readthedocs.org/css/readthedocs-doc-embed.css',
            ]
        yaml.dump(user_config, open('mkdocs.yml', 'w'))

        # RTD javascript writing

        READTHEDOCS_DATA = {
            'project': project.slug,
            'version': self.version.slug,
            'language': project.language,
            'page': None,
            'theme': "readthedocs",
            'docroot': docs_dir,
            'source_suffix': ".md",
            'api_host': getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org'),
        }
        data_json = json.dumps(READTHEDOCS_DATA, indent=4)
        data_ctx = Context({
            'data_json': data_json,
            'current_version': READTHEDOCS_DATA['version'],
            'slug': READTHEDOCS_DATA['project'],
            'html_theme': READTHEDOCS_DATA['theme'],
            'pagename': None,
        })
        data_string = template_loader.get_template(
            'doc_builder/data.js.tmpl'
        ).render(data_ctx)

        data_file = open(os.path.join(docs_dir, 'readthedocs-data.js'), 'w+')
        data_file.write(data_string)
        data_file.close()

        include_ctx = Context({
            'global_analytics_code': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
            'user_analytics_code': project.analytics_code,
        })
        include_string = template_loader.get_template(
            'doc_builder/include.js.tmpl'
        ).render(include_ctx)
        include_file = open(os.path.join(docs_dir, 'readthedocs-dynamic-include.js'), 'w+')
        include_file.write(include_string)
        include_file.close()

        # Actual build

        if project.use_virtualenv:
            build_command = "%s build --site-dir=site --theme=mkdocs" % (
                project.venv_bin(version=self.version.slug,
                                 bin='mkdocs')
            )
        else:
            build_command = "mkdocs build --site-dir=site --theme=mkdocs"
        results = run(build_command, shell=True)

        # Index Search
        page_list = []
        log.info(LOG_TEMPLATE.format(project=self.version.project.slug, version=self.version.slug, msg='Indexing files'))
        for root, dirnames, filenames in os.walk(site_path):
            for filename in filenames:
                if fnmatch.fnmatch(filename, '*.html'):
                    full_path = os.path.join(root, filename.lstrip('/'))
                    relative_path = os.path.join(root.replace(site_path, '').lstrip('/'), filename.lstrip('/')).rstrip('.html')
                    html = self._parse_html(full_path)
                    page_list.append(
                        {'content': html, 'path': relative_path, 'title': relative_path.rstrip('/index'), 'headers': [], 'sections': []}
                    )

        data = {
            'page_list': page_list,
            'version_pk': self.version.pk,
            'project_pk': self.version.project.pk
        }
        log_msg = ' '.join([page['path'] for page in page_list])
        log.info("(Search Index) Sending Data: %s [%s]" % (self.version.project.slug, log_msg))
        apiv2.index_search.post({'data': data})

        return results
