import re
import os

from django.template.loader import render_to_string
from django.template import Template, Context
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from doc_builder.base import BaseBuilder
from projects.utils import safe_write, run


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
    'badge_revsys': {{ project.sponsored }}
}
if 'html_context' in locals():
    html_context.update(context)
else:
    html_context = context
"""

TEMPLATE_DIR = '%s/readthedocs/templates/sphinx' % settings.SITE_ROOT
STATIC_DIR = '%s/_static' % TEMPLATE_DIR

class Builder(BaseBuilder):

    def _whitelisted(self, version):
        """Modify the given ``conf.py`` file from a whitelisted user's project.
        For now, this just adds the RTD template directory to ``templates_path``.
        """
        project = version.project
        #Open file for appending.
        try:
            outfile = open(project.conf_file(version.slug), 'a')
        except IndexError:
            print "Nothing to white list, no conf.py"
            return
        outfile.write("\n")
        rtd_ctx = Context({
            'verisons': project.active_versions(),
            'current_version': version,
            'project': project,
            'settings': settings,
            'static_path': STATIC_DIR,
            'template_path': TEMPLATE_DIR,
        })
        rtd_string = Template(RTD_CONF_ADDITIONS).render(rtd_ctx)
        outfile.write(rtd_string)
        outfile.close()

    def _sanitize(self, version):
        project = version.project
        conf_template =  render_to_string('sphinx/conf.py.conf',
                                          {'project': project,
                                           'template_dir': TEMPLATE_DIR,
                                            'badge': project.sponsored
                                            })
        rtd_ctx = Context({
            'verisons': project.active_versions(),
            'current_version': version,
            'project': project,
            'settings': settings,
            'static_path': STATIC_DIR,
            'template_path': TEMPLATE_DIR,
        })
        rtd_string = Template(RTD_CONF_ADDITIONS).render(rtd_ctx)
        conf_template = conf_template + "\n" + rtd_string
        safe_write(project.conf_file(version.slug), conf_template)

    def clean(self, version):
        try:
            if version.project.whitelisted and version.project.is_imported:
                print "Project whitelisted"
                self._whitelisted(version)
            else:
                print "Writing conf to disk"
                self._sanitize(version)
        except (OSError, SiteProfileNotAvailable, ObjectDoesNotExist):
            try:
                print "Writing conf to disk on error."
                self._sanitize(version)
            except (OSError, IOError):
                print "Conf file not found. Error writing to disk."
                return ('','Conf file not found. Error writing to disk.',-1)

    def build(self, version):
        project = version.project
        os.chdir(version.project.conf_dir(version.slug))
        if project.use_virtualenv and project.whitelisted:
            build_command = '%s -b html . _build/html' % project.venv_bin(version=version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b html . _build/html"
        build_results = run(build_command)
        return build_results
