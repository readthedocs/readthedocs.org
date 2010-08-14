import os
import fnmatch
from celery.decorators import task
from projects.models import Project
from projects.utils import get_project_path, find_file

#@task
def update_docs(slug, type='git'):
    project = Project.objects.get(slug=slug)
    path = get_project_path(project)
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    if os.path.exists(os.path.join(path, project.slug)):
        os.chdir(project.slug)
        if type is 'git':
            command = 'git reset --hard origin/master'
            print command
            os.system(command)
    else:
        if type is 'git':
            command = 'git clone %s.git %s' % (project.github_repo, project.slug)
            print command
            os.system(command)
        elif type is 'hg':
            os.system('hg clone ')
    build_docs(path)


def build_docs(path):
    os.chdir(path)
    matches = find_file('Makefile')
    if len(matches) == 1:
        make_dir = matches[0].replace('/Makefile', '')
        os.chdir(make_dir)
        os.system('make html')
