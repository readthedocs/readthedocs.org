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

def run(*commands):
    """
    Run one or more commands, and return ``(status, out, err)``.
    If more than one command is given, then this is equivalent to
    chaining them together with ``&&``; if all commands succeed, then
    ``(status, out, err)`` will represent the last successful command.
    If one command failed, then ``(status, out, err)`` will represent
    the failed command.
    """
    environment = os.environ.copy()
    cwd = os.getcwd()
    if not commands:
        raise ValueError("run() requires one or more command-line strings")

    for command in commands:
        print("Running: '%s'" % command)
        try:
            p = subprocess.Popen(command.split(), shell=False, cwd=cwd,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 env=environment)

            out, err = p.communicate()
            ret = p.returncode
        except:
            out = ''
            err = traceback.format_exc()
            ret = -1
            print "fail!"

        # If returncode is nonzero, bail out
        if ret != 0:
            break

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
    # FIXME: Pull this from the site configuration
    template_dir = '/home/docs/sites/readthedocs.com/checkouts/tweezers/templates/sphinx'

    # Expression to match the templates_path line
    # FIXME: This could fail if the statement spans multiple lines
    # (but will work as long as the first line has the opening '[')
    templates_re = re.compile('(#*\s*templates_path\s*=\s*\[)(.*)')

    # Get all lines from the conf.py file
    lines = open(conf_filename).readlines()

    # Write all lines back out, making any necessary modifications
    outfile = open(conf_filename, 'w')
    for line in lines:
        match = templates_re.match(line)
        if match:
            left, right = match.groups()
            line = left + "'%s', " % template_dir + right
        outfile.write(line)
    outfile.close()

