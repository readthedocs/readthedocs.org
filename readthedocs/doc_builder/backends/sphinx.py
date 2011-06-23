import os
import shutil

from django.template.loader import render_to_string
from django.template import Template, Context
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import safe_write, run
from core.utils import copy_to_app_servers


RTD_CONF_ADDITIONS = """
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
if 'html_theme' in locals():
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
    'versions': [{% for version in verisons %}
    ("{{ version.slug }}", "{{ version.get_absolute_url }}"),{% endfor %}
    ],
    'slug': '{{ project.slug }}',
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
        outfile = open(project.conf_file(self.version.slug), 'a')
        outfile.write("\n")
        rtd_ctx = Context({
                'verisons': project.active_versions(),
                'current_version': self.version,
                'project': project,
                'settings': settings,
                'static_path': STATIC_DIR,
                'template_path': TEMPLATE_DIR,
                })
        rtd_string = Template(RTD_CONF_ADDITIONS).render(rtd_ctx)
        outfile.write(rtd_string)

    def _sanitize(self):
        project = self.version.project
        conf_template = render_to_string('sphinx/conf.py.conf',
                                         {'project': project,
                                          'template_dir': TEMPLATE_DIR,
                                          'badge': project.sponsored
                                          })
        rtd_ctx = Context({
            'verisons': project.active_versions(),
            'current_version': self.version,
            'project': project,
            'settings': settings,
            'static_path': STATIC_DIR,
            'template_path': TEMPLATE_DIR,
        })
        rtd_string = Template(RTD_CONF_ADDITIONS).render(rtd_ctx)
        conf_template = conf_template + "\n" + rtd_string
        safe_write(project.conf_file(self.version.slug), conf_template)

    def clean(self):
        try:
            if self.version.project.whitelisted and self.version.project.is_imported:
                print "Project whitelisted"
                self._whitelisted()
            else:
                print "Writing conf to disk"
                self._sanitize()
        except (OSError, SiteProfileNotAvailable, ObjectDoesNotExist):
            try:
                print "Writing conf to disk on error."
                self._sanitize()
            except (OSError, IOError):
                print "Conf file not found. Error writing to disk."
                return ('', 'Conf file not found. Error writing to disk.', -1)

    @restoring_chdir
    def build(self):
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        if project.use_virtualenv and project.whitelisted:
            build_command = '%s -b html . _build/html' % project.venv_bin(
                version=self.version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b html . _build/html"
        build_results = run(build_command)
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results

    def move(self):
        project = self.version.project
        if project.full_build_path(self.version.slug):
            target = project.rtd_build_path(self.version.slug)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                print "Copying docs to remote server."
                copy_to_app_servers(project.full_build_path(self.version.slug), target)
            else:
                if os.path.exists(target):
                    shutil.rmtree(target)
                print "Copying docs on the local filesystem"
                shutil.copytree(project.full_build_path(self.version.slug), target)
        else:
            print "Not moving docs, because the build dir is unknown."
