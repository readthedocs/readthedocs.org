"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""
import decimal
import fnmatch
import os
import getpass
import re
import shutil

from celery.decorators import periodic_task, task
from celery.task.schedules import crontab
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist

from builds.models import Build, Version
from doc_builder import loading as builder_loading
from projects.exceptions import ProjectImportError
from projects.utils import slugify_uniquely
from projects.exceptions import ProjectImportError
from projects.models import Project, ImportedFile
from projects.utils import run, slugify_uniquely
from tastyapi import client
from vcs_support.base import get_backend

ghetto_hack = re.compile(r'(?P<key>.*)\s*=\s*u?\[?[\'\"](?P<value>.*)[\'\"]\]?')

@task
def update_docs(pk, record=True, pdf=True, version_pk=None, touch=False):
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

    if version:
        versions = [version]
    else:
        versions = [None]# + list(project.versions.filter(active=True, uploaded=False))

    for version in versions:
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
    result = client.import_project(project)
    if result:
        print "Project imported from Django Packages!"


def update_imported_docs(project, version):
    """
    Check out or update the given project's repository.
    """
    if not project.vcs_repo:
        raise ProjectImportError("Repo type '%s' unknown" % project.repo_type)
    if version:
        print 'Checking out version %s: %s' % (version.slug, version.identifier)
        project.vcs_repo.checkout(version.identifier)
    else:
        print 'Updating to latest revision'
        project.vcs_repo.update()

    if version:
        version_slug = version.slug
    else:
        version_slug = 'latest'
    #Do Virtualenv bits:
    if project.use_virtualenv:
        run('virtualenv --no-site-packages %s' % project.venv_path(version=version_slug))
        run('%s install sphinx sphinxcontrib-issuetracker' % project.venv_bin(version=version_slug,
                                                      bin='pip'))

        os.chdir(project.user_checkout_path)
        run('%s setup.py install' % project.venv_bin(version=version_slug,
                                                          bin='python'))

    # check tags/version
    try:
        if project.vcs_repo.supports_tags:
            transaction.enter_transaction_management(True)
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
                    print "Failed to create version (tag): %s" % e
                    transaction.rollback()
            transaction.leave_transaction_management()
        if project.vcs_repo.supports_branches:
            transaction.enter_transaction_management(True)
            branches = project.vcs_repo.get_branches()
            old_branches = Version.objects.filter(project=project).values_list('identifier', flat=True)
            for branch in branches:
                if branch.identifier in old_branches:
                    continue
                slug = slugify_uniquely(Version, branch.verbose_name, 'slug', 255, project=project)
                try:
                    Version.objects.get_or_create(
                        project=project,
                        slug=slug,
                        identifier=branch.identifier,
                        verbose_name=branch.verbose_name
                    )
                except Exception, e:
                    print "Failed to create version (branch): %s" % e
                    transaction.rollback()
            transaction.leave_transaction_management()
            #Kill deleted branches
            Version.objects.filter(project=project).exclude(identifier__in=old_branches).delete()
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
            Build.objects.create(
                project=project,
                success=successful,
                output=html_output[1],
                error=html_output[2],
                version=version
            )

        if pdf:
            pdf_builder = builder_loading.get('pdf')()
            pdf_builder.build(project, version)
    if successful:
        move_docs(project, version)
        if version:
            version.built = True
            version.save()
    return html_output

def move_docs(project, version):
    if project.full_build_path:
        version_slug = 'latest'
        if version:
            version_slug = version.slug
        target = os.path.join(project.rtd_build_path, version_slug)
        if getattr(settings, "MULTIPLE_APP_SERVERS", None):
            copy_to_app_servers(project.full_build_path, target)
        else:
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(project.full_build_path, target)
    else:
        print "Not moving docs, because the build dir is unknown."

def copy_to_app_servers(full_build_path, target):
    #You should be checking for this above.
    servers = settings.MULTIPLE_APP_SERVERS
    for server in servers:
        ret = os.system("rsync -e 'ssh -T' -av --delete %s/ %s@%s:%s" % (full_build_path, getpass.getuser(), server, target))
        if ret != 0:
            print "COPY ERROR: out: %s err: %s" % (ret[1], ret[2])


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


@task
def unzip_files(dest_file, html_path):
    if not os.path.exists(html_path):
        os.makedirs(html_path)
    else:
        shutil.rmtree(html_path)
        os.makedirs(html_path)
    run('unzip -of %s -d %s' % (dest_file, html_path))
