from celery.decorators import task
from celery.task.schedules import crontab
from celery.decorators import periodic_task

from projects.constants import SCRAPE_CONF_SETTINGS, DEFAULT_THEME_CHOICES
from projects.models import Project, ImportedFile
from projects.utils import  find_file, run, sanitize_conf

from builds.models import Build

import decimal
import os
import re
import glob
import fnmatch


ghetto_hack = re.compile(r'(?P<key>.*)\s*=\s*u?\[?[\'\"](?P<value>.*)[\'\"]\]?')

@task
def update_docs(pk, record=True):
    """
    A Celery task that updates the documentation for a project.
    """
    project = Project.objects.live().get(pk=pk)
    if project.skip:
        return

    path = project.user_doc_path
    if not os.path.exists(path):
        os.makedirs(path)

    if project.is_imported:
        try:
            update_imported_docs(project)
        except (RuntimeError, NotImplementedError):
            print("Error updating imported docs, skipping build.")
            return
        else:
            scrape_conf_file(project)
    else:
        update_created_docs(project)

    # kick off a build
    (ret, out, err) = build_docs(project)
    if not 'no targets are out of date.' in out:
        if record:
            Build.objects.create(project=project, success=ret==0, output=out, error=err)
        if ret == 0:
            print "Build OK"
        else:
            print "Build ERROR"
            print err
    else:
        print "Build Unchanged"


def update_imported_docs(project):
    path = project.user_doc_path
    os.chdir(path)

    # TODO: Could probably use some better error handling here, in
    # case one of the below commands fails for any reason

    # If project directory already exists, do an update/fetch/merge
    if os.path.exists(os.path.join(path, project.slug)):
        os.chdir(project.slug)
        if project.repo_type == 'hg':
            run('hg fetch')
            run('hg update -C .')
        elif project.repo_type == 'git':
            run('git --git-dir=.git fetch')
            run('git --git-dir=.git reset --hard origin/master')
        elif project.repo_type == 'svn':
            run('svn revert')
            run('svn up')
        elif project.repo_type == 'bzr':
            run('bzr revert')
            run('bzr up')
        else:
            raise NotImplementedError("Repo type '%s' unknown" % project.repo_type)

    # Project directory doesn't exist, so do a clone/checkout/branch
    else:
        repo = project.repo
        if project.repo_type == 'hg':
            command = 'hg clone %s %s' % (repo, project.slug)
        elif project.repo_type == 'git':
            repo = repo.replace('.git', '')
            command = 'git clone --depth=1 %s.git %s' % (repo, project.slug)
        elif project.repo_type == 'svn':
            command = 'svn checkout %s %s' % (repo, project.slug)
        elif project.repo_type == 'bzr':
            command = 'bzr checkout %s %s' % (repo, project.slug)
        else:
            raise NotImplementedError("Repo type '%s' unknown" % project.repo_type)
        # Run the command and raise an exception on error
        status, out, err = run(command)
        if status != 0:
            raise RuntimeError("Failed to get code from repository: '%s'" % repo)


    fileify(project_slug=project.slug)


def scrape_conf_file(project):
    try:
        conf_dir = project.find('conf.py')[0]
    except IndexError:
        print("Could not find conf.py in %s" % project)
        return
    else:
        conf_dir = conf_dir.replace('/conf.py', '')

    os.chdir(conf_dir)
    lines = open('conf.py').readlines()
    data = {}
    for line in lines:
        match = ghetto_hack.search(line)
        if match:
            data[match.group(1).strip()] = match.group(2).strip()
    project.copyright = data['copyright']
    project.theme = data.get('html_theme', 'default')
    #if project.theme not in [x[0] for x in DEFAULT_THEME_CHOICES]:
        #project.theme = 'default'
    project.suffix = data.get('source_suffix', '.rst')
    #project.extensions = data.get('extensions', '').replace('"', "'")
    project.path = os.getcwd()

    try:
        project.version = decimal.Decimal(data.get('version', '0.1.0'))
    except decimal.InvalidOperation:
        project.version = ''

    project.save()


def update_created_docs(project):
    # grab the root path for the generated docs to live at
    path = project.user_doc_path

    doc_root = os.path.join(path, project.slug, 'docs')

    if not os.path.exists(doc_root):
        os.makedirs(doc_root)

    project.path = doc_root
    project.save()

    project.write_index()

    for file in project.files.all():
        file.write_to_disk()


def build_docs(project):
    """
    A helper function for the celery task to do the actual doc building.
    """
    if project.whitelisted:
        sanitize_conf(project.conf_filename)
    else:
        project.write_to_disk()

    try:
        makes = [makefile for makefile in project.find('Makefile') if 'doc' in makefile]
        make_dir = makes[0].replace('/Makefile', '')
        os.chdir(make_dir)
        (ret, out, err) = run('make html')
    except IndexError:
        os.chdir(project.path)
        (ret, out, err) = run('sphinx-build -b html . _build/html')
    return (ret, out, err)


@task
def fileify(project_slug):
    project = Project.objects.get(slug=project_slug)
    path = project.full_html_path
    if path:
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if fnmatch.fnmatch(filename, '*.html'):
                    dirpath =  os.path.join(root.replace(path, '').lstrip('/'), filename.lstrip('/'))
                    file, new = ImportedFile.objects.get_or_create(project=project,
                                                path=dirpath,
                                                name=filename)
@periodic_task(run_every=crontab(hour="*", minute="10", day_of_week="*"))
def update_docs_pull():
    for project in Project.objects.live():
        print "Building %s" % project
        update_docs(pk=project.pk, record=False)
