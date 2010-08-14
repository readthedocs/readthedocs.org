from celery.decorators import task
from celery.task.schedules import crontab  
from celery.decorators import periodic_task  

from projects.models import Project, Conf
from projects.utils import  find_file, run

import os
import re
import glob
import fnmatch


ghetto_hack = re.compile(r'(?P<key>.*)\s*=\s*u?[\'\"](?P<value>.*)[\'\"]')

@task
def update_docs(slug, type='git'):
    """
    A Celery task that updates the documentation for a project.
    """
    project = Project.objects.get(slug=slug)
    path = project.user_doc_path
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    if os.path.exists(os.path.join(path, project.slug)):
        os.chdir(project.slug)
        if type is 'git':
            command = 'git fetch && git reset --hard origin/master'
            print command
            run(command)
    else:
        if type is 'git':
            repo = project.github_repo
            repo.relace('.git', '')
            command = 'git clone %s.git %s' % (repo, project.slug)
            print command
            run(command)
    build_docs(project)


def build_docs(project):
    """
    A helper function for the celery task to do the actual doc building.
    """
    conf_dir = project.find('conf.py')[0].replace('/conf.py', '')
    os.chdir(conf_dir)
    lines = open('conf.py').readlines()
    data = {}
    for line in lines:
        for we_care in ['copyright', 'project', 'version', 'release', 'html_theme']:
            match = ghetto_hack.search(line)
            if match:
                data[match.group(1).strip()] = match.group(2).strip()
    conf = Conf.objects.get_or_create(project=project)[0]
    conf.copyright = data['copyright']
    conf.version = data.get('version', 0.1)
    conf.theme = data.get('html_theme', 'default')
    conf.path = os.getcwd()
    conf.save()

    project.write_conf()

    make_dir = project.find('Makefile')[0].replace('/Makefile', '')
    os.chdir(make_dir)
    os.system('make html')

#@periodic_task(run_every=crontab(hour="*", minute="*/30", day_of_week="*"))  
@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))  
def update_docs_pull():
    for project in Project.objects.all():
        print "Building %s" % project
        build_docs(project)

