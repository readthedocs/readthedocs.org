import os
import fnmatch
from django.conf import settings
import subprocess

def get_project_path(project):
    return os.path.join(settings.DOCROOT, project.user.username, project.slug)

def find_file(file):
    matches = []
    for root, dirnames, filenames in os.walk('.'):
      for filename in fnmatch.filter(filenames, file):
          matches.append(os.path.join(root, filename))
    return matches
