import os
import fnmatch
from django.conf import settings
import commands

def get_project_path(project):
    return os.path.join(settings.DOCROOT, project.user.username, project.slug)

def find_file(file):
    matches = []
    for root, dirnames, filenames in os.walk('.'):
      for filename in fnmatch.filter(filenames, file):
          matches.append(os.path.join(root, filename))
    return matches

def run(command):
    os.system(command)
    """
    return commands.get_output(command)
    p = subprocess.Popen(command, cwd=os.getcwd(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    ret = p.returncode
    return (ret, out, err)
    """

