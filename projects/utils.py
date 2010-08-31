import subprocess
import os
import fnmatch
import traceback
import re

from django.conf import settings

from projects.libs.diff_match_patch import diff_match_patch

def find_file(file):
    matches = []
    for root, dirnames, filenames in os.walk('.'):
      for filename in fnmatch.filter(filenames, file):
          matches.append(os.path.join(root, filename))
    return matches

def run(command):
    environment = os.environ.copy()
    cwd = os.getcwd()
    command_list = [cmd for cmd in command.split(' ')]
    try:
        p = subprocess.Popen(command_list, shell=False, cwd=cwd,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=environment)

        out, err = p.communicate()
        ret = p.returncode
    except:
        out = ''
        err = traceback.format_exc()
        ret = -1
        print "fail!"

    return (ret, out, err)


dmp = diff_match_patch()

def diff(txt1, txt2):
    """Create a 'diff' from txt1 to txt2."""
    patch = dmp.patch_make(txt1, txt2)
    return dmp.patch_toText(patch)

def safe_write(filename, contents):
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    fh = open(filename, 'w')
    fh.write(contents.encode('utf-8', 'ignore'))
    fh.close()

def sanitize_conf(conf_filename):
    """Modify the given ``conf.py`` file from a whitelisted project. For now,
    this just adds the RTD template directory to ``templates_path``.
    """
    # The template directory for RTD
    template_dir = '%s/templates/sphinx' % settings.SITE_ROOT

    # Expression to match the templates_path line
    # FIXME: This could fail if the statement spans multiple lines
    # (but will work as long as the first line has the opening '[')
    templates_re = re.compile('(#*\s*templates_path\s*=\s*\[)(.*)')

    # Get all lines from the conf.py file
    lines = open(conf_filename).readlines()

    lines_matched = 0
    # Write all lines back out, making any necessary modifications
    outfile = open(conf_filename, 'w')
    for line in lines:
        match = templates_re.match(line)
        if match:
            left, right = match.groups()
            line = left + "'%s', " % template_dir + right
            lines_matched += 1
        outfile.write(line)
    outfile.close()
    return lines_matched
