import re
import os

from django.template.loader import render_to_string
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from doc_builder.base import BaseBuilder
from projects.utils import diff, dmp, safe_write, run


HTML_CONTEXT = """
should_badge = %s
if 'html_context' in locals():
    html_context.update({'badge_revsys': should_badge})
else:
    html_context = {
        'slug': '%s',
        'badge_revsys': should_badge
    }
"""


class Builder(BaseBuilder):

    def _whitelisted(self, project):
        """Modify the given ``conf.py`` file from a whitelisted user's project.
        For now, this just adds the RTD template directory to ``templates_path``.
        """
        conf_filename = project.conf_filename
        # The template directory for RTD
        template_dir = '%s/templates/sphinx' % settings.SITE_ROOT

        # Expression to match the templates_path line
        # FIXME: This could fail if the statement spans multiple lines
        # (but will work as long as the first line has the opening '[')
        templates_re = re.compile('(\s*templates_path\s*=\s*\[)(.*)')

        # Get all lines from the conf.py file
        lines = open(conf_filename).readlines()

        lines_matched = 0
        # Write all lines back out, making any necessary modifications
        outfile = open(conf_filename, 'w')
        for line in lines:
            match = templates_re.match(line)
            if match:
                left, right = match.groups()
                line = left + "'%s', " % template_dir + right + "\n"
                lines_matched += 1
            outfile.write(line)
        if not lines_matched:
            outfile.write('templates_path = ["%s"]' % template_dir)
        outfile.write(HTML_CONTEXT % (project.sponsored, project.slug))
        outfile.close()
        return lines_matched

    def _sanitize(self, project):
        conf_template =  render_to_string('sphinx/conf.py',
                                          {'project': project,
                                            'badge': project.sponsored
                                            })
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

    def build(self, project):
        build_results = self.run_make_command(project,
                                              'make html',
                                              'sphinx-build -b html . _build/html')
        return build_results
