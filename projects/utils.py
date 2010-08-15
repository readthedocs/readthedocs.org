import subprocess
import os
import fnmatch
import traceback

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
