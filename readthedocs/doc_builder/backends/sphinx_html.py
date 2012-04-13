import collections
import glob
import os
import shutil
import codecs
import zipfile
import logging

from django.template.loader import render_to_string
from django.template import Template, Context
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from sphinx.config import Config
from sphinx.util.tags import Tags

from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import safe_write, run
from core.utils import copy_to_app_servers, copy_file_to_app_servers

log = logging.getLogger(__name__)


RTD_CONF_ADDITIONS = """
{% load projects_tags %}
#Add RTD Template Path.
if 'templates_path' in locals():
    templates_path.insert(0, '{{ template_path }}')
else:
    templates_path = ['{{ template_path }}', 'templates', '_templates', '.templates']

#Add RTD Static Path. Add to the end because it overwrites previous files.
if 'html_static_path' in locals():
    html_static_path.append('{{ static_path }}')
else:
    html_static_path = ['_static', '{{ static_path }}']

#Add RTD CSS File only if they aren't overriding it already
using_rtd_theme = False
if project == "Python":
    #Do nothing for Python theme-wise
    pass
elif 'html_theme' in locals():
    if html_theme in ['default']:
        if not 'html_style' in locals():
            html_style = 'rtd.css'
            html_theme = 'default'
            html_theme_options = {}
            using_rtd_theme = True
else:
    html_style = 'rtd.css'
    html_theme = 'default'
    html_theme_options = {}
    using_rtd_theme = True

#Add sponsorship and project information to the template context.
context = {
    'using_theme': using_rtd_theme,
    'current_version': "{{ current_version.slug }}",
    'MEDIA_URL': "{{ settings.MEDIA_URL }}",
    'versions': [{% for version in versions|sort_version_aware %}
    ("{{ version.slug }}", "{{ version.absolute_url }}"),{% endfor %}
    ],
    'slug': '{{ project.slug }}',
    'name': u'{{ project.name }}',
    'badge_revsys': {{ project.sponsored }},
    'analytics_code': '{{ project.analytics_code }}',
}
if 'html_context' in locals():
    html_context.update(context)
else:
    html_context = context
"""

TEMPLATE_DIR = '%s/readthedocs/templates/sphinx' % settings.SITE_ROOT
STATIC_DIR = '%s/_static' % TEMPLATE_DIR


class Builder(BaseBuilder):
    """
    The parent for most sphinx builders.

    Also handles the default sphinx output of html.
    """

    def _whitelisted(self):
        """Modify the given ``conf.py`` file from a whitelisted user's project.
        """
        project = self.version.project
        #Open file for appending.
        outfile = codecs.open(project.conf_file(self.version.slug), encoding='utf-8', mode='a')
        outfile.write("\n")
        rtd_ctx = Context({
                'versions': project.api_versions(),
                'current_version': self.version,
                'project': project,
                'settings': settings,
                'static_path': STATIC_DIR,
                'template_path': TEMPLATE_DIR,
                })
        rtd_string = Template(RTD_CONF_ADDITIONS).render(rtd_ctx)
        outfile.write(rtd_string)

    def clean(self):
        log.info("Project whitelisted")
        try:
            self._whitelisted()
        except (OSError, SiteProfileNotAvailable, ObjectDoesNotExist):
            log.error("Conf file not found. Error writing to disk.", exc_info=True)
            return ('', 'Conf file not found. Error writing to disk.', -1)

    @restoring_chdir
    def build(self):
        project = self.version.project
        conf_dir = project.conf_dir(self.version.slug)
        conf_file = project.conf_file(self.version.slug)

        translations = self._get_translations(conf_dir, conf_file)
        compile_commands = self._compile_commands(translations)
        build_commands = self._build_commands(translations, project)

        os.chdir(conf_dir)
        build_results = run(*(compile_commands + build_commands))

        self._zip_html()
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False

        return build_results

    def _build_commands(self, translations, project):
        if project.use_virtualenv:
            sphinx_build = project.venv_bin(version=self.version.slug,
                                            bin='sphinx-build')
        else:
            sphinx_build = 'sphinx-build'
        options = ' -E' if self.force else ''

        results = ['%s -b html %s . _build/html/en' % (sphinx_build, options)]
        for lang in translations:
            results.append('%s -b html -D language=%s . _build/html/%s' % (
                    sphinx_build, lang + options, lang))
        return results

    def _compile_commands(self, translations):
        results = []
        for po_files in translations.values():
            for po in po_files:
                mo = os.path.splitext(po)[0] + '.mo'
                results.append('msgfmt %s -o %s' % (po, mo))
        return results

    def _get_translations(self, conf_dir, conf_file):
        config = Config(conf_dir, conf_file, {}, Tags(None))
        config.init_values()

        results = collections.defaultdict(list)

        for dir_ in config.locale_dirs:
            for lang in os.listdir(os.path.join(conf_dir, dir_)):
                po_files = glob.glob(
                    os.path.join(conf_dir, dir_, lang, 'LC_MESSAGES', '*.po'))
                results[lang].extend(po_files)
        log.info('Available translations: [%s]' % ','.join(results.keys()))

        return results

    @restoring_chdir
    def _zip_html(self):
        from_path = self.version.project.full_build_path(self.version.slug)
        from_file = os.path.join(from_path, '%s.zip' % self.version.project.slug)
        to_path = self.version.project.checkout_path(self.version.slug)
        to_file = os.path.join(to_path, '%s.zip' % self.version.project.slug)

        log.info("Creating zip file from %s" % from_path)
        # Create a <slug>.zip file containing all files in file_path
        os.chdir(from_path)
        archive = zipfile.ZipFile(to_file, 'w')
        for root, subfolders, files in os.walk('.'):
            for file in files:
                to_write = os.path.join(root, file)
                archive.write(
                    filename=to_write, 
                    arcname=os.path.join("%s-%s" % (self.version.project.slug, self.version.slug), to_write)
                )
        archive.close()

        return to_file

    def move(self):
        project = self.version.project
        if project.full_build_path(self.version.slug):
            #Copy the html files.
            target = project.rtd_build_path(self.version.slug)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                log.info("Copying docs to remote server.")
                copy_to_app_servers(project.full_build_path(self.version.slug), target)
            else:
                if os.path.exists(target):
                    shutil.rmtree(target)
                log.info("Copying docs on the local filesystem")
                shutil.copytree(project.full_build_path(self.version.slug), target)

            #Copy the zip file.
            to_path = os.path.join(settings.MEDIA_ROOT,
                   'htmlzip',
                   project.slug,
                   self.version.slug)
            to_file = os.path.join(to_path, '%s.zip' % project.slug)
            from_path = project.checkout_path(self.version.slug)
            from_file = os.path.join(from_path, '%s.zip' % project.slug)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                copy_file_to_app_servers(from_file, to_file)
            else:
                if not os.path.exists(to_path):
                    os.makedirs(to_path)
                run('mv -f %s %s' % (from_file, to_file))
        else:
            log.warning("Not moving docs, because the build dir is unknown.")
