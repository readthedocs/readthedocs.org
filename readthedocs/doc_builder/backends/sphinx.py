import os
import shutil
import codecs
import logging
import zipfile

from django.template import Template, Context
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from builds import utils as version_utils
from core.utils import copy_to_app_servers, copy_file_to_app_servers
from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run
from tastyapi import apiv2

log = logging.getLogger(__name__)


RTD_CONF_ADDITIONS = """
{% load projects_tags %}
#Add RTD Template Path.
if 'templates_path' in globals():
    templates_path.insert(0, '{{ template_path }}')
else:
    templates_path = ['{{ template_path }}', 'templates', '_templates',
                      '.templates']

# Add RTD Static Path. Add to the end because it overwrites previous files.
if 'html_static_path' in globals():
    html_static_path.append('{{ static_path }}')
else:
    html_static_path = ['_static', '{{ static_path }}']

# Add RTD Theme Path. 
if 'html_theme_path' in globals():
    html_theme_path.append('{{ template_path }}')
else:
    html_theme_path = ['_themes', '{{ template_path }}']

# Add RTD Theme only if they aren't overriding it already
using_rtd_theme = False
if 'html_theme' in globals():
    if html_theme in ['default']:
        # Allow people to bail with a hack of having an html_style
        if not 'html_style' in globals():
            html_theme = 'sphinx_rtd_theme'
            html_style = None
            html_theme_options = {}
            using_rtd_theme = True
else:
    html_theme = 'sphinx_rtd_theme'
    html_style = None
    html_theme_options = {}
    using_rtd_theme = True

# Force theme on setting
if globals().get('RTD_NEW_THEME', False):
    html_theme = 'sphinx_rtd_theme'
    html_style = None
    html_theme_options = {}
    using_rtd_theme = True

if globals().get('RTD_OLD_THEME', False):
    html_style = 'rtd.css'
    html_theme = 'default'

#Add project information to the template context.
context = {
    'using_theme': using_rtd_theme,
    'html_theme': html_theme,
    'current_version': "{{ current_version }}",
    'MEDIA_URL': "{{ settings.MEDIA_URL }}",
    'PRODUCTION_DOMAIN': "{{ settings.PRODUCTION_DOMAIN }}",
    'versions': [{% for version in versions|sort_version_aware %}
    ("{{ version.slug }}", "/{{ version.project.language }}/{{ version.slug}}/"),{% endfor %}
    ],
    'downloads': [ {% for key, val in downloads.items %}
    ("{{ key }}", "{{ val }}"),{% endfor %}
    ],
    'slug': '{{ project.slug }}',
    'name': u'{{ project.name }}',
    'rtd_language': u'{{ project.language }}',
    'canonical_url': '{{ project.clean_canonical_url }}',
    'analytics_code': '{{ project.analytics_code }}',
    'single_version': {{ project.single_version }},
    'conf_py_path': '{{ conf_py_path }}',
    'api_host': '{{ api_host }}',
    'github_user': '{{ github_user }}',
    'github_repo': '{{ github_repo }}',
    'github_version': '{{ github_version }}',
    'display_github': {{ display_github }},
    'READTHEDOCS': True,
    'using_theme': (html_theme == "default"),
    'new_theme': (html_theme == "sphinx_rtd_theme"),
}
if 'html_context' in globals():
    html_context.update(context)
else:
    html_context = context

# Add custom RTD extension
if 'extensions' in globals():
    extensions.append("readthedocs_ext.readthedocs")
else:
    extensions = ["readthedocs_ext.readthedocs"]
"""

TEMPLATE_DIR = '%s/readthedocs/templates/sphinx' % settings.SITE_ROOT
STATIC_DIR = '%s/_static' % TEMPLATE_DIR


class Builder(BaseBuilder):
    """
    The parent for most sphinx builders.

    Also handles the default sphinx output of html.
    """

    def _whitelisted(self, **kwargs):
        """Modify the given ``conf.py`` file from a whitelisted user's project.
        """
        project = self.version.project
        #Open file for appending.
        outfile = codecs.open(project.conf_file(self.version.slug),
                              encoding='utf-8', mode='a')
        outfile.write("\n")
        conf_py_path = version_utils.get_conf_py_path(self.version)
        remote_version = version_utils.get_vcs_version_slug(self.version)
        github_info = version_utils.get_github_username_repo(self.version)
        bitbucket_info = version_utils.get_bitbucket_username_repo(self.version)
        if github_info[0] is None:
            display_github = False
        else:
            display_github = True
        if bitbucket_info[0] is None:
            display_bitbucket = False
        else:
            display_bitbucket = True

        rtd_ctx = Context({
            'versions': project.api_versions(),
            'downloads': self.version.get_downloads(pretty=True),
            'current_version': self.version.slug,
            'project': project,
            'settings': settings,
            'static_path': STATIC_DIR,
            'template_path': TEMPLATE_DIR,
            'conf_py_path': conf_py_path,
            'downloads': apiv2.version(self.version.pk).downloads.get()['downloads'],
            'api_host': getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org'),
            # GitHub
            'github_user': github_info[0],
            'github_repo': github_info[1],
            'github_version':  remote_version,
            'display_github': display_github,
            # BitBucket
            'bitbucket_user': bitbucket_info[0],
            'bitbucket_repo': bitbucket_info[1],
            'bitbucket_version':  remote_version,
            'display_bitbucket': display_bitbucket,
        })
        rtd_string = Template(RTD_CONF_ADDITIONS).render(rtd_ctx)
        outfile.write(rtd_string)

    def clean(self, **kwargs):
        try:
            self._whitelisted()
        except (OSError, SiteProfileNotAvailable, ObjectDoesNotExist):
            log.error("Conf file not found. Error writing to disk.",
                      exc_info=True)
            return ('', 'Conf file not found. Error writing to disk.', -1)

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        force_str = " -E " if self.force else ""
        if project.use_virtualenv:
            build_command = "%s %s -b readthedocs -D language=%s . _build/html " % (
                project.venv_bin(version=self.version.slug,
                                 bin='sphinx-build'),
                force_str,
                project.language)
        else:
            build_command = ("sphinx-build %s -b readthedocs -D language=%s . _build/html"
                             % (force_str, project.language))
        build_results = run(build_command, shell=True)
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results

    def move(self, **kwargs):
        project = self.version.project
        if project.full_build_path(self.version.slug):
            #Copy the html files.
            target = project.rtd_build_path(self.version.slug)
            if "_" in project.slug:
                new_slug = project.slug.replace('_', '-')
                new_target = target.replace(project.slug, new_slug)
                #Only replace 1, so user_builds doesn't get replaced >:x
                targets = [target, new_target]
            else:
                targets = [target]
            for target in targets:
                if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                    log.info("Copying docs to remote server.")
                    copy_to_app_servers(
                        project.full_build_path(self.version.slug), target)
                else:
                    if os.path.exists(target):
                        shutil.rmtree(target)
                    log.info("Copying docs on the local filesystem")
                    shutil.copytree(
                        project.full_build_path(self.version.slug), target)

                #Copy the zip file.
                to_path = os.path.join(settings.MEDIA_ROOT, 'htmlzip',
                                       project.slug, self.version.slug)
                to_file = os.path.join(to_path, '%s.zip' % project.slug)
                from_path = project.checkout_path(self.version.slug)
                from_file = os.path.join(from_path, '%s.zip' % project.slug)
                if os.path.exists(from_file):
                    if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                        copy_file_to_app_servers(from_file, to_file)
                    else:
                        if not os.path.exists(to_path):
                            os.makedirs(to_path)
                        run('mv -f %s %s' % (from_file, to_file))
        else:
            log.warning("Not moving docs, because the build dir is unknown.")
