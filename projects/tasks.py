"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""

from builds.models import Build, Version
from celery.decorators import periodic_task, task
from celery.task.schedules import crontab
from doc_builder import loading as builder_loading
from django.db import transaction
from projects.exceptions import ProjectImportError
from projects.utils import slugify_uniquely
from vcs_support.base import get_backend
from django.conf import settings
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from projects.exceptions import ProjectImportError
from projects.models import Project, ImportedFile
from projects.utils import run, slugify_uniquely
import decimal
import fnmatch
import os
import re
import shutil

ghetto_hack = re.compile(r'(?P<key>.*)\s*=\s*u?\[?[\'\"](?P<value>.*)[\'\"]\]?')

@task
def update_docs(pk, record=True, pdf=False, version_pk=None, touch=False):
    """
    A Celery task that updates the documentation for a project.
    """

    ###
    # Handle passed in arguments
    ###
    project = Project.objects.live().get(pk=pk)
    print "Building %s" % project
    if version_pk:
        version = Version.objects.get(pk=version_pk)
    else:
        version = None
    path = project.user_doc_path
    if not os.path.exists(path):
        os.makedirs(path)

    with project.repo_lock(30):
        if project.is_imported:
            try:
                update_imported_docs(project, version)
            except ProjectImportError, err:
                print("Error importing project: %s. Skipping build." % err)
                return
            else:
                scrape_conf_file(project)
        else:
            update_created_docs(project)

        # kick off a build
        (ret, out, err) = build_docs(project, version, pdf, record, touch)
        if not 'no targets are out of date.' in out:
            if ret == 0:
                print "Build OK"
            else:
                print "Build ERROR"
                print err
        else:
            print "Build Unchanged"


def update_imported_docs(project, version):
    """
    Check out or update the given project's repository.
    """
    if not project.vcs_repo:
        raise ProjectImportError("Repo type '%s' unknown" % project.repo_type)
    if version:
        print 'Checking out version %s' % version.identifier
        project.vcs_repo.checkout(version.identifier)
    else:
        print 'Updating to latest revision'
        project.vcs_repo.update()

        # check tags/version
        try:
            if project.vcs_repo.supports_tags:
                tags = project.vcs_repo.get_tags()
                old_tags = Version.objects.filter(project=project).values_list('identifier', flat=True)
                for tag in tags:
                    if tag.identifier in old_tags:
                        continue
                    slug = slugify_uniquely(Version, tag.verbose_name, 'slug', 255, project=project)
                    try:
                        Version.objects.get_or_create(
                            project=project,
                            slug=slug,
                            identifier=tag.identifier,
                            verbose_name=tag.verbose_name
                        )
                    except Exception, e:
                        print "Failed to create version: %s" % e
                        transaction.rollback()
        except ValueError, e:
            print "Error getting tags: %s" % e


    fileify(project_slug=project.slug)


def scrape_conf_file(project):
    """Locate the given project's ``conf.py`` file and extract important
    settings, including copyright, theme, source suffix and version.
    """

    #This is where we actually find the conf.py, so we can't use
    #the value from the project :)
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
    project.suffix = data.get('source_suffix', '.rst')
    project.path = os.getcwd()

    try:
        project.version = decimal.Decimal(data.get('version'))
    except (TypeError, decimal.InvalidOperation):
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


def build_docs(project, version, pdf, record, touch):
    """
    A helper function for the celery task to do the actual doc building.
    """
    if not project.path:
        return ('','Conf file not found.',-1)

    html_builder = builder_loading.get('html')()
    if touch:
        html_builder.touch(project)

    html_builder.clean(project)
    html_output = html_builder.build(project, version)
    successful = (html_output[0] == 0)
    if not 'no targets are out of date.' in html_output[1]:
        if record:
                Build.objects.create(project=project, success=successful,
                                 output=html_output[1], error=html_output[2])
        if successful:
            move_docs(project, version)
            if version:
                version.built = True
                version.save()

        if pdf or project.build_pdf:
            pdf_builder = builder_loading.get('pdf')()
            pdf_builder.build(project, version)
    return html_output

def move_docs(project, version):
    if project.full_build_path:
        version_slug = 'latest'
        if version:
            version_slug = version.slug
        target = os.path.join(project.rtd_build_path, version_slug)
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(project.full_build_path, target)
    else:
        print "Not moving docs, because the build dir is unknown."

def fileify(project_slug):
    project = Project.objects.get(slug=project_slug)
    path = project.full_build_path
    if path:
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if fnmatch.fnmatch(filename, '*.html'):
                    dirpath =  os.path.join(root.replace(path, '').lstrip('/'),
                                            filename.lstrip('/'))
                    file, new = ImportedFile.objects.get_or_create(project=project,
                                                path=dirpath,
                                                name=filename)


@periodic_task(run_every=crontab(hour="2", minute="10", day_of_week="*"))
def update_docs_pull(record=False, pdf=False, touch=False):
    for project in Project.objects.live():
        update_docs(pk=project.pk, record=record, pdf=pdf, touch=touch)
