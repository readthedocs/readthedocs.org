"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""

from django.conf import settings
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist

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

latex_re = re.compile('the LaTeX files are in (.*)\.')

class ProjectImportError (Exception):
    """Failure to import a project from a repository."""
    pass


@task
def update_docs(pk, record=True, pdf=False):
    """
    A Celery task that updates the documentation for a project.
    """
    project = Project.objects.live().get(pk=pk)
    if project.skip:
        print "Skipping %s" % project
        return
    print "Building %s" % project
    path = project.user_doc_path
    if not os.path.exists(path):
        os.makedirs(path)

    if project.is_imported:
        try:
            update_imported_docs(project)
        except ProjectImportError, err:
            print("Error importing project: %s. Skipping build." % err)
            return
        else:
            scrape_conf_file(project)
    else:
        update_created_docs(project)

    # kick off a build
    (ret, out, err) = build_docs(project, pdf)
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
    """
    Check out or update the given project's repository.
    """
    path = project.user_doc_path
    os.chdir(path)
    repo = project.repo

    # Commands to be run to checkout/update
    cmds = []

    # If project directory already exists, do an update/fetch/merge
    if os.path.exists(os.path.join(path, project.slug)):
        os.chdir(project.slug)
        if project.repo_type == 'hg':
            cmds.append('hg pull')
            cmds.append('hg update -C .')

        elif project.repo_type == 'git':
            cmds.append('git --git-dir=.git fetch')
            cmds.append('git --git-dir=.git reset --hard origin/master')

        elif project.repo_type == 'svn':
            cmds.append('svn revert .')
            cmds.append('svn up --accept theirs-full')

        elif project.repo_type == 'bzr':
            cmds.append('bzr revert')
            cmds.append('bzr up')

        else:
            raise ProjectImportError("Repo type '%s' unknown" % project.repo_type)

    # Project directory doesn't exist, so do a clone/checkout/branch
    else:
        if project.repo_type == 'hg':
            cmds.append('hg clone %s %s' % (repo, project.slug))

        elif project.repo_type == 'git':
            repo = repo.replace('.git', '').strip('/')
            cmds.append('git clone --depth=1 %s.git %s' % (repo, project.slug))

        elif project.repo_type == 'svn':
            cmds.append('svn checkout %s %s' % (repo, project.slug))

        elif project.repo_type == 'bzr':
            cmds.append('bzr checkout %s %s' % (repo, project.slug))

        else:
            raise ProjectImportError("Repo type '%s' unknown" % project.repo_type)

    # Run the command(s) and raise an exception on error
    status, out, err = run(*cmds)
    if status != 0:
        raise ProjectImportError("Failed to get code from repo: '%s'" % repo)

    fileify(project_slug=project.slug)


def scrape_conf_file(project):
    """Locate the given project's ``conf.py`` file and extract important
    settings, including copyright, theme, source suffix and version.
    """
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
    project.copyright = data.get('copyright', 'Unknown')
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


def build_docs(project, pdf):
    """
    A helper function for the celery task to do the actual doc building.
    """
    if not project.path:
        return ('','Conf file not found.',-1)
    try:
        # If user has a profile and is whitelisted,
        # allow full evaluation of their project's conf.py
        profile = project.user.get_profile()
        if profile.whitelisted:
            print "Project whitelisted"
            sanitize_conf(project.conf_filename)
        # Otherwise, just write the safe-to-evaluate version
        else:
            print "Writing conf to disk"
            project.write_to_disk()
    except (OSError, SiteProfileNotAvailable, ObjectDoesNotExist):
        try:
            print "Writing conf to disk"
            project.write_to_disk()
        except (OSError, IOError):
            print "Conf file not found. Error writing to disk."
            return ('','Conf file not found. Error writing to disk.',-1)


    try:
        makes = [makefile for makefile in project.find('Makefile') if 'doc' in makefile]
        make_dir = makes[0].replace('/Makefile', '')
        os.chdir(make_dir)
        html_results = run('make html')
        if pdf:
            latex_results = run('make latex')
            match = latex_re.search(latex_results[1])
            if match:
                latex_dir = match.group(1).strip()
                os.chdir(latex_dir)
                pdf_results = run('make')
                pdf = glob.glob('*.pdf')[0]
                run('ln -s %s %s/%s.pdf' % (os.path.join(os.getcwd(), pdf),
                                            settings.MEDIA_ROOT,
                                            project.slug
                                           ))
    except IndexError:
        os.chdir(project.path)
        html_results = run('sphinx-build -b html . _build/html')
    return html_results


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


@periodic_task(run_every=crontab(hour="2", minute="10", day_of_week="*"))
def update_docs_pull(pdf=False):
    for project in Project.objects.live():
        update_docs(pk=project.pk, record=False, pdf=pdf)
