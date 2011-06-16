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
from sphinx.ext.intersphinx import fetch_inventory
import redis

from builds.models import Build, Version
from doc_builder import loading as builder_loading
from projects.exceptions import ProjectImportError
from projects.utils import slugify_uniquely, purge_version, DictObj
from projects.exceptions import ProjectImportError
from projects.models import Project, ImportedFile
from projects.utils import run, slugify_uniquely, mkversion, safe_write
from tastyapi import client
from vcs_support.base import get_backend

ghetto_hack = re.compile(r'(?P<key>.*)\s*=\s*u?\[?[\'\"](?P<value>.*)[\'\"]\]?')

@task
def remove_dir(path):
    print "Removing %s" % path
    shutil.rmtree(path)

@task
def update_docs(pk, record=True, pdf=True, man=True, version_pk=None, touch=False):
    """
    A Celery task that updates the documentation for a project.
    """

    ###
    # Handle passed in arguments
    ###
    project = Project.objects.live().get(pk=pk)
    print "Building %s" % project
    if version_pk:
        versions = [Version.objects.get(pk=version_pk)]
    else:
        branch = project.default_branch or project.vcs_repo().fallback_branch
        latest = Version.objects.filter(project=project, slug='latest')
        if len(latest):
            #Handle changing of latest's branch
            latest = latest[0]
            if not latest.identifier == branch:
                latest.identifier = branch
                latest.save()
            versions = [latest]
        else:
            versions = [Version.objects.create(project=project,
                            identifier=branch,
                            slug='latest',
                            verbose_name='latest')]

    for version in versions:
        #Make Dirs
        path = project.doc_path
        if not os.path.exists(path):
            os.makedirs(path)
        with project.repo_lock(30):
            if project.is_imported:
                try:
                    confpy = update_imported_docs(project, version)
                except ProjectImportError, err:
                    print("Error importing project: %s. Skipping build." % err)
                    return
                else:
                    if confpy == -1:
                        return -1
                    scrape_conf_file(version)
            else:
                update_created_docs(project)

            # kick off a build
            (ret, out, err) = build_docs(project, version, pdf, man, record, touch)
            if not 'no targets are out of date.' in out:
                if ret == 0:
                    print "Build OK"
                    purge_version(version, subdomain=True, mainsite=True, cname=True)
                    update_intersphinx(version.pk)
                    print "Purged %s" % version
                else:
                    print "Build ERROR"
                    print err
            else:
                print "Build Unchanged"
    try:
        result = client.import_project(project)
        if result:
            print "Project imported from Django Packages!"
    except:
        print "Importing from Django Packages Errored."



def update_imported_docs(project, version):
    """
    Check out or update the given project's repository.
    """
    if not project.vcs_repo():
        raise ProjectImportError("Repo type '%s' unknown" % project.repo_type)
    if version:
        print 'Checking out version %s: %s' % (version.slug, version.identifier)
        version_slug = version.slug
        version_repo = project.vcs_repo(version_slug)
        version_repo.checkout(version.identifier)
    else:
        print 'Updating to latest revision'
        version_slug = 'latest'
        version_repo = project.vcs_repo(version_slug)
        version_repo.update()

    #Break early without a conf file.
    if not project.conf_file(version.slug):
        print "Conf File Missing. Skipping."
        return -1

    #Do Virtualenv bits:
    if project.use_virtualenv and project.whitelisted:
        run('virtualenv --no-site-packages %s' % project.venv_path(version=version_slug))
        run('%s install sphinx' % project.venv_bin(version=version_slug,
                                                      bin='pip'))
        if project.requirements_file:
            os.chdir(project.checkout_path(version_slug))
            run('%s install -r %s' % (project.venv_bin(version=version_slug, bin='pip'),
                                    project.requirements_file))
        os.chdir(project.checkout_path(version_slug))
        run('%s setup.py install --force' % project.venv_bin(version=version_slug,
                                                          bin='python'))

    # check tags/version
    try:
        if version_repo.supports_tags:
            transaction.enter_transaction_management(True)
            tags = version_repo.get_tags()
            old_tags = Version.objects.filter(project=project).values_list('identifier', flat=True)
            for tag in tags:
                if tag.identifier in old_tags:
                    continue
                slug = slugify_uniquely(Version, tag.verbose_name, 'slug', 255, project=project)
                try:
                    ver, created = Version.objects.get_or_create(
                        project=project,
                        slug=slug,
                        identifier=tag.identifier,
                        verbose_name=tag.verbose_name
                    )
                    print "New tag found: %s" % ver
                    highest = project.highest_version[1]
                    ver_obj = mkversion(ver)
                    if highest and ver_obj and ver_obj > highest:
                        print "Highest verison known, building docs"
                        update_docs.delay(ver.project.pk, version_pk=ver.pk)
                except Exception, e:
                    print "Failed to create version (tag): %s" % e
                    transaction.rollback()
            transaction.leave_transaction_management()
        if version_repo.supports_branches:
            transaction.enter_transaction_management(True)
            branches = version_repo.get_branches()
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
                    print "New branch found: %s" % ver
                except Exception, e:
                    print "Failed to create version (branch): %s" % e
                    transaction.rollback()
            transaction.leave_transaction_management()
            #Kill deleted branches
            Version.objects.filter(project=project).exclude(identifier__in=old_branches).delete()
    except ValueError, e:
        print "Error getting tags: %s" % e
        return


    fileify(version)


def scrape_conf_file(version):
    """Locate the given project's ``conf.py`` file and extract important
    settings, including copyright, theme, source suffix and version.
    """
    #This is where we actually find the conf.py, so we can't use
    #the value from the project :)
    project = version.project
    try:
        conf_file = project.conf_file(version.slug)
    except IndexError:
        print("Could not find conf.py in %s" % project)
        return -1
    else:
        conf_dir = conf_file.replace('/conf.py', '')

    os.chdir(conf_dir)
    lines = open('conf.py').readlines()
    data = {}
    for line in lines:
        match = ghetto_hack.search(line)
        if match:
            data[match.group(1).strip()] = match.group(2).strip()
    project.copyright = data.get('copyright', 'Unknown')
    project.theme = data.get('html_theme', 'default')
    if len(project.theme) > 20:
        project.theme = 'default'
    project.suffix = data.get('source_suffix', '.rst')
    project.path = os.getcwd()

    try:
        project.version = decimal.Decimal(data.get('version'))
    except (TypeError, decimal.InvalidOperation):
        project.version = ''

    project.save()


def update_created_docs(project):
    # grab the root path for the generated docs to live at
    path = project.doc_path

    doc_root = os.path.join(path, 'checkouts', 'latest', 'docs')

    if not os.path.exists(doc_root):
        os.makedirs(doc_root)

    project.path = doc_root
    project.save()
    #Touch a conf.py
    safe_write(os.path.join(project.path, 'conf.py'), '')

    project.write_index()

    for file in project.files.all():
        file.write_to_disk()


def build_docs(project, version, pdf, man, record, touch):
    """
    A helper function for the celery task to do the actual doc building.
    """
    if not project.conf_file(version.slug):
        return ('','Conf file not found.',-1)

    html_builder = builder_loading.get(project.documentation_type)()
    if touch:
        html_builder.touch(version)
    html_builder.clean(version)
    html_output = html_builder.build(version)
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
            pdf_builder = builder_loading.get('sphinx_pdf')()
            pdf_builder.build(version)
        if man:
            man_builder = builder_loading.get('sphinx_man')()
            man_builder.build(version)
    if successful:
        move_docs(project, version)
        if version:
            version.active = True
            version.built = True
            version.save()
    return html_output

def move_docs(project, version):
    if project.full_build_path(version.slug):
        target = project.rtd_build_path(version.slug)
        if getattr(settings, "MULTIPLE_APP_SERVERS", None):
            copy_to_app_servers(project.full_build_path(version.slug), target)
        else:
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(project.full_build_path(version.slug), target)
    else:
        print "Not moving docs, because the build dir is unknown."

def copy_to_app_servers(full_build_path, target):
    #You should be checking for this above.
    servers = settings.MULTIPLE_APP_SERVERS
    for server in servers:
        os.system("ssh %s@%s mkdir -p %s" % (getpass.getuser(), server, target))
        ret = os.system("rsync -e 'ssh -T' -av --delete %s/ %s@%s:%s" % (full_build_path, getpass.getuser(), server, target))
        if ret != 0:
            print "COPY ERROR: out: %s err: %s" % (ret[1], ret[2])


def fileify(version):
    project = version.project
    path = project.rtd_build_path(version.slug)
    if path:
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if fnmatch.fnmatch(filename, '*.html'):
                    dirpath =  os.path.join(root.replace(path, '').lstrip('/'),
                                            filename.lstrip('/'))
                    file, new = ImportedFile.objects.get_or_create(project=project,
                                                path=dirpath,
                                                name=filename)


#@periodic_task(run_every=crontab(hour="2", minute="10", day_of_week="*"))
def update_docs_pull(record=False, pdf=False, man=False, touch=False):
    for project in Project.objects.live():
        try:
            update_docs(pk=project.pk, record=record, pdf=pdf, man=man, touch=touch)
        except:
            print "failed"


@task
def unzip_files(dest_file, html_path):
    if not os.path.exists(html_path):
        os.makedirs(html_path)
    else:
        shutil.rmtree(html_path)
        os.makedirs(html_path)
    run('unzip -o %s -d %s' % (dest_file, html_path))
    copy_to_app_servers(html_path, html_path)

@task
def update_intersphinx(version_pk):
    version = Version.objects.get(pk=version_pk)
    path = version.project.rtd_build_path(version.slug)
    if not path:
        print "ERR: %s has no path" % version
        return None
    app = DictObj()
    app.srcdir = path
    try:
        inv = fetch_inventory(app, app.srcdir, 'objects.inv')
    except TypeError:
        print "Failed to fetch inventory for %s" % version
        return None
    # I'm entirelty not sure this is even close to correct.
    # There's a lot of info I'm throwing away here; revisit later?
    for keytype in inv:
        for term in inv[keytype]:
            try:
                _, _, url, title = inv[keytype][term]
                if not title or title == '-':
                    if '#' in url:
                        title = url.rsplit('#')[-1]
                    else:
                        title = url
                find_str = "rtd-builds/latest"
                latest = url.find(find_str)
                url = url[latest + len(find_str) + 1:]
                url = "http://%s.readthedocs.org/en/latest/%s" % (version.project.slug, url)
                save_term(version, term, url, title)
                if '.' in term:
                    save_term(version, term.split('.')[-1], url, title)
            except Exception, e: #Yes, I'm an evil person.
                print "*** Failed updating %s: %s" % (term, e)

def save_term(version, term, url, title):
    redis_obj = redis.Redis(**settings.REDIS)
    print "Inserting %s: %s" % (term, url)
    lang = "en"
    project_slug = version.project.slug
    version_slug = version.slug
    redis_obj.sadd('redirects:v3:%s:%s:%s:%s' % (lang, project_slug,
                                         version_slug, term), url)
    redis_obj.setnx('redirects:v3:%s:%s:%s:%s:%s' % (lang, project_slug,
                                             version_slug, term, url), 1)
