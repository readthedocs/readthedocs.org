from celery.decorators import task
from celery.task.schedules import crontab
from celery.decorators import periodic_task

from projects.constants import SCRAPE_CONF_SETTINGS
from projects.models import Project, Conf
from projects.utils import  find_file, run

import os
import re
import glob
import fnmatch


ghetto_hack = re.compile(r'(?P<key>.*)\s*=\s*u?[\'\"](?P<value>.*)[\'\"]')

@task
def update_docs(pk):
    project = Project.objects.get(pk=pk)
    if project.is_imported:
        update_imported_docs(project)
        scrape_conf_file(project)
    else:
        updated_created_docs(project)

    # kick off a build
    build_docs(project)


def update_imported_docs(project):
    """
    A Celery task that updates the documentation for a project.
    """
    path = project.user_doc_path
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    if os.path.exists(os.path.join(path, project.slug)):
        os.chdir(project.slug)
        if project.repo_type is 'hg':
            command = 'hg update -C -r . '
        else:
            command = 'git fetch && git reset --hard origin/master'
        print command
        run(command)
    else:
        repo = project.repo
        if project.repo_type is 'hg':
            command = 'hg clone %s %s' % (repo, project.slug)
        else:
            repo.replace('.git', '')
            command = 'git clone %s.git %s' % (repo, project.slug)
        print command
        run(command)


def scrape_conf_file(project):
    conf_dir = project.find('conf.py')[0].replace('/conf.py', '')
    os.chdir(conf_dir)
    lines = open('conf.py').readlines()
    data = {}
    for line in lines:
        for we_care in SCRAPE_CONF_SETTINGS:
            match = ghetto_hack.search(line)
            if match:
                data[match.group(1).strip()] = match.group(2).strip()
    conf = Conf.objects.get_or_create(project=project)[0]
    conf.copyright = data['copyright']
    conf.theme = data.get('html_theme', 'default')
    conf.suffix = data.get('source_suffix', '.rst')
    conf.path = os.getcwd()
    conf.save()

    project.version = data.get('version', '0.1.0')
    project.save()


def update_created_docs(project):
    # grab the root path for the generated docs to live at
    path = self.user_doc_path

    doc_root = os.path.join(path, project.slug, 'docs')

    # TODO: write files


def build_docs(project):
    """
    A helper function for the celery task to do the actual doc building.
    """
    project.write_conf()

    try:
        makes = [makefile for makefile in project.find('Makefile') if 'doc' in makefile]
        make_dir = makes[0].replace('/Makefile', '')
        os.chdir(make_dir)
        print make_dir
        os.system('make html')
    except IndexError:
        os.chdir(project.conf.path)
        os.system('sphinx-build -b html . _build')


#@periodic_task(run_every=crontab(hour="*", minute="*/30", day_of_week="*"))
@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def update_docs_pull():
    for project in Project.objects.all():
        print "Building %s" % project
        try:
            build_docs(project)
        except Exception, e:
            update_docs(pk=project.pk)
            print e
