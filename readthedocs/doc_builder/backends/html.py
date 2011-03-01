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

#Add sponsorship and project information to the template context.
context = {
    'using_theme': using_rtd_theme,
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

    def _whitelisted(self, project):
        """Modify the given ``conf.py`` file from a whitelisted user's project.
        For now, this just adds the RTD template directory to ``templates_path``.
        """
        #Open file for appending.
        outfile = open(project.conf_filename, 'a')
        outfile.write("\n")
        rtd_ctx = Context({
            'verisons': project.active_versions(),
            'project': project,
            'static_path': STATIC_DIR,
            'template_path': TEMPLATE_DIR,
        })
        rtd_string = Template(RTD_CONF_ADDITIONS).render(rtd_ctx)
        outfile.write(rtd_string)
        outfile.close()

    def _sanitize(self, project):
        conf_template =  render_to_string('sphinx/conf.py',
                                          {'project': project,
                                           'template_dir': TEMPLATE_DIR,
                                            'badge': project.sponsored
                                            })
        rtd_ctx = Context({
            'verisons': project.active_versions(),
            'project': project,
            'static_path': STATIC_DIR,
            'template_path': TEMPLATE_DIR,
        })
        rtd_string = Template(RTD_CONF_ADDITIONS).render(rtd_ctx)
        conf_template = conf_template + "\n" + rtd_string
        safe_write(project.conf_filename, conf_template)


    def clean(self, project):
        try:
            profile = project.user.get_profile()
            if profile.whitelisted:
                print "Project whitelisted"
                self._whitelisted(project)
            else:
                print "Writing conf to disk"
                self._sanitize(project)
        except (OSError, SiteProfileNotAvailable, ObjectDoesNotExist):
            try:
                print "Writing conf to disk"
                self._sanitize(project)
            except (OSError, IOError):
                print "Conf file not found. Error writing to disk."
                return ('','Conf file not found. Error writing to disk.',-1)

    def build(self, project, version):
        if not version:
            version_slug = 'latest'
        else:
            version_slug = version.slug
        os.chdir(project.path)
        if project.use_virtualenv:
            build_command = '%s -b html . _build/html' % project.venv_bin(version=version_slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b html . _build/html"
        build_results = run(build_command)
        return build_results
