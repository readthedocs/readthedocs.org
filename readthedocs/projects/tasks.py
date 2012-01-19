"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""
import decimal
import fnmatch
import os
import re
import shutil
import json

from celery.decorators import task
from django.db import transaction
from django.conf import settings
import redis
from sphinx.ext.intersphinx import fetch_inventory


from builds.models import Version
from doc_builder import loading as builder_loading
from doc_builder.base import restoring_chdir
from projects.exceptions import ProjectImportError
from projects.models import ImportedFile, Project
from projects.utils import (
    DictObj,
    mkversion,
    purge_version,
    run,
    safe_write,
    slugify_uniquely,
    )
from tastyapi import client as tastyapi_client
from tastyapi import api
from core.utils import copy_to_app_servers, run_on_app_servers

ghetto_hack = re.compile(
    r'(?P<key>.*)\s*=\s*u?\[?[\'\"](?P<value>.*)[\'\"]\]?')


@task
def remove_dir(path):
    """
    Remove a directory on the build/celery server.

    This is mainly a wrapper around shutil.rmtree so that app servers
    can kill things on the build server.
    """
    print "Removing %s" % path
    shutil.rmtree(path)


@task
@restoring_chdir
def update_docs(pk, record=True, pdf=True, man=True, epub=True, version_pk=None, force=False, **kwargs):
    """
    The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported or we created it.
    Then it will build the html docs and other requested parts.
    It also handles clearing the varnish cache.
    """

    ###
    # Handle passed in arguments
    ###
    update_output = kwargs.get('update_output', {})
    project_data = api.project(pk).get()
    del project_data['users']
    del project_data['resource_uri']
    del project_data['absolute_url']
    project = Project(**project_data)
    def new_save(*args, **kwargs):
        #fields = [(field, field.value_to_string(self)) for field in self._meta.fields]
        print "*** Called save on a non-real object."
        #print fields
        #raise TypeError('Not a real model')
        return 0
    project.save = new_save
    print "Building %s" % project
    if version_pk:
        version_data = api.version(version_pk).get()
    else:
        branch = project.default_branch or project.vcs_repo().fallback_branch
        version_data = api.version(project.slug).get(slug='latest')['objects'][0]
    del version_data['resource_uri']
    version_data['project'] = project
    version = Version(**version_data)
    version.save = new_save

    #Lots of course correction.
    to_save = False
    if not version.verbose_name:
        version_data['verbose_name'] = 'latest'
        to_save = True
    if not version.active:
        version_data['active'] = True
        to_save = True
    if version.identifier != branch:
        version_data['identifier'] = branch
        to_save = True
    if to_save:
        api.version(version.pk).put(version_data)

    if record:
        #Create Build Object.
        build = Build.objects.create(
            project=project,
            version=version,
            type='html',
            state='triggered',
        )
    else:
        build = {}

    #Make Dirs
    path = project.doc_path
    if not os.path.exists(path):
        os.makedirs(path)
    with project.repo_lock(30):
        if project.is_imported:
            try:
                update_output = update_imported_docs(project, version)
            except ProjectImportError, err:
                print("Error importing project: %s. Skipping build." % err)
                return False

            scrape_conf_file(version)
        else:
            update_created_docs(project)

        # kick off a build
        if record:
            build.state = 'building'
            build.save()
        (ret, out, err) = build_docs(project=project, build=build, version=version,
                                     pdf=pdf, man=man, epub=epub,
                                     record=record, force=force, update_output=update_output)
        if not 'no targets are out of date.' in out:
            if ret == 0:
                print "HTML Build OK"
                purge_version(version, subdomain=True,
                              mainsite=True, cname=True)
                symlink_cname(version)
                update_intersphinx(version.pk)
                #send_notifications(version)
                print "Purged %s" % version
            else:
                print "HTML Build ERROR"
        else:
            print "Build Unchanged"

    # Try importing from Open Comparison sites.
    try:
        result = tastyapi_client.import_project(project)
        if result:
            print "Project imported from Open Comparison!"
        else:
            print "Project failed to import from Open Comparison!"

    except:
        print "Importing from Open Comparison Errored."

    # Try importing from Crate
    try:
        result = tastyapi_client.import_crate(project)
        if result:
            print "Project imported from Crate!"
        else:
            print "Project failed to import from Crate!"

    except:
        print "Importing from Crate Errored."

    return True


def update_imported_docs(project, version):
    """
    Check out or update the given project's repository.
    """
    update_docs_output = {}
    if not project.vcs_repo():
        raise ProjectImportError("Repo type '{repo_type}' unknown".format(
                repo_type=project.repo_type))

    if version:
        print 'Checking out version {slug}: {identifier}'.format(
            slug=version.slug, identifier=version.identifier)
        version_slug = version.slug
        version_repo = project.vcs_repo(version_slug)
        update_docs_output['checkout'] = version_repo.checkout(version.identifier)
    else:
        print 'Updating to latest revision'
        version_slug = 'latest'
        version_repo = project.vcs_repo(version_slug)
        update_docs_output['checkout'] = version_repo.update()

    #Break early without a conf file.
    if not project.conf_file(version.slug):
        raise ProjectImportError("Conf File Missing. Skipping.")

    #Do Virtualenv bits:
    if project.use_virtualenv and project.whitelisted:
        update_docs_output['venv'] = run('{cmd} --no-site-packages {path}'.format(
                cmd='virtualenv',
                path=project.venv_path(version=version_slug)))
        update_docs_output['sphinx'] = run('{cmd} install -U sphinx'.format(
                cmd=project.venv_bin(version=version_slug, bin='pip')))

        if project.requirements_file:
            os.chdir(project.checkout_path(version_slug))
            update_docs_output['requirements'] = run('{cmd} install -r {requirements}'.format(
                    cmd=project.venv_bin(version=version_slug, bin='pip'),
                    requirements=project.requirements_file))
        os.chdir(project.checkout_path(version_slug))
        update_docs_output['install'] = run('{cmd} setup.py install --force'.format(
                cmd=project.venv_bin(version=version_slug, bin='python')))

    # check tags/version
    #XXX:dc: what in this block raises the values error?
    try:
        if version_repo.supports_tags:
            transaction.enter_transaction_management(True)
            tags = version_repo.tags
            old_tags = [obj['identifier'] for obj in api.version.get(project__slug=project.slug, limit=50)['objects']]
            for tag in tags:
                if tag.identifier in old_tags:
                    continue
                slug = slugify_uniquely(Version, tag.verbose_name,
                                        'slug', 255, project=project)
                try:

                    api.version.post(
                        project="/api/v1/project/%s/" % project.pk,
                        slug=slug,
                        identifier=tag.identifier,
                        verbose_name=tag.verbose_name
                    )
                    print "New tag found: %s" % ver
                    highest = project.highest_version['version']
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
            branches = version_repo.branches
            old_branches = [obj['identifier'] for obj in api.version.get(project__slug=project.slug, limit=50)['objects']]
            for branch in branches:
                if branch.identifier in old_branches:
                    continue
                slug = slugify_uniquely(Version, branch.verbose_name,
                                        'slug', 255, project=project)
                try:
                    api.version.post(
                        project="/api/v1/project/%s/" % project.pk,
                        slug=slug,
                        identifier=branch.identifier,
                        verbose_name=branch.verbose_name
                    )
                    print "New branch found: %s" % ver
                except Exception, e:
                    print "Failed to create version (branch): %s" % e
                    transaction.rollback()
            transaction.leave_transaction_management()
            #TODO: Kill deleted branches
    except ValueError, e:
        print "Error getting tags: %s" % e

    #TODO: Find a better way to handle indexing.
    #fileify(version)
    return update_docs_output


def scrape_conf_file(version):
    """
    Locate the given project's ``conf.py`` file and extract important
    settings, including copyright, theme, source suffix and version.
    """
    #This is where we actually find the conf.py, so we can't use
    #the value from the project :)
    project = version.project
    project_data = api.project(project.pk).get()

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
    project_data['copyright'] = data.get('copyright', 'Unknown')
    project_data['theme'] = data.get('html_theme', 'default')
    if len(project.theme) > 20:
        project_data['theme'] = 'default'
    project_data['suffix'] = data.get('source_suffix', '.rst')
    project_data['path'] = os.getcwd()

    try:
        project_data['version'] = str(decimal.Decimal(data.get('version')))
    except (TypeError, decimal.InvalidOperation):
        project_data['version'] = ''

    api.project(project.pk).put(project_data)


def update_created_docs(project):
    """
    Handle generating the docs for projects hosted on RTD.
    """
    # grab the root path for the generated docs to live at
    path = project.doc_path

    doc_root = os.path.join(path, 'checkouts', 'latest', 'docs')

    if not os.path.exists(doc_root):
        os.makedirs(doc_root)

    project.path = doc_root
    #project.save()
    #Touch a conf.py
    safe_write(os.path.join(project.path, 'conf.py'), '')

    project.write_index()

    for file in project.files.all():
        file.write_to_disk()


def build_docs(project, build, version, pdf, man, epub, record, force, update_output={}):
    """
    This handles the actual building of the documentation and DB records
    """
    if not project.conf_file(version.slug):
        return ('', 'Conf file not found.', -1)

    html_builder = builder_loading.get(project.documentation_type)(version)
    if force:
        html_builder.force()
    html_builder.clean()
    html_output = html_builder.build()
    successful = (html_output[0] == 0)
    if successful:
        html_builder.move()
        if version:
            version_data = api.version(version.pk).get()
            version_data['active'] = True
            version_data['built'] = True
            #Need to delete this because a bug in tastypie breaks on the users list.
            del version_data['project']
            api.version(version.pk).put(version_data)
    if html_builder.changed:
        if record:
            output_data = error_data = ''
            #Grab all the text from updating the code via VCS.
            for key in ['checkout', 'venv', 'sphinx', 'requirements', 'install']:
                data = update_output.get(key, None)
                if data:
                    output_data += data[1]
                    error_data += data[2]
            #Update build.
            build.success = successful
            build.setup = output_data
            build.setup_error = error_data
            build.output = html_output[1]
            build.error = html_output[2]
            build.state = 'finished'
            build.project='/api/v1/project/%s/" % project.pk
            build.version='/api/v1/version/%s/" % version.pk
            build.save()
            ))
        if pdf:
            pdf_builder = builder_loading.get('sphinx_pdf')(version)
            latex_results, pdf_results = pdf_builder.build()
            if record:
                Build.objects.create(
                    project=project,
                    success=pdf_results[0] == 0,
                    type='pdf',
                    setup=latex_results[1],
                    setup_error=latex_results[2],
                    output=pdf_results[1],
                    error=pdf_results[2],
                    version=version
                )
            #PDF Builder is oddly 2-steped, and stateful for now
            #pdf_builder.move(version)
        #XXX:dc: all builds should have their output checked
        if man:
            man_builder = builder_loading.get('sphinx_man')(version)
            man_builder.build()
            man_builder.move()
        if epub:
            epub_builder = builder_loading.get('sphinx_epub')(version)
            epub_builder.build()
            epub_builder.move()
    return html_output


def fileify(version):
    """
    Create ImportedFile objects for all of a version's files.

    This is a prereq for indexing the docs for search.
    """
    project = version.project
    path = project.rtd_build_path(version.slug)
    if path:
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if fnmatch.fnmatch(filename, '*.html'):
                    dirpath = os.path.join(root.replace(path, '').lstrip('/'),
                                            filename.lstrip('/'))
                    api.importedfile.post(
                        project="/api/v1/project/%s/" % project.pk,
                        path=dirpath,
                        name=filename)


#@periodic_task(run_every=crontab(hour="2", minute="10", day_of_week="*"))
def update_docs_pull(record=False, pdf=False, man=False, force=False):
    """
    A high-level interface that will update all of the projects.

    This is mainly used from a cronjob or management command.
    """
    for project in Project.objects.live():
        try:
            update_docs(
                pk=project.pk, record=record, pdf=pdf, man=man, force=force)
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
    version_data = api.version(version_pk).get()
    del version_data['resource_uri']
    project_data = version_data['project']
    del project_data['users']
    del project_data['resource_uri']
    del project_data['absolute_url']
    project = Project(**project_data)
    version_data['project'] = project
    version = Version(**version_data)

    object_file = version.project.find('objects.inv', version.slug)[0]
    path = version.project.rtd_build_path(version.slug)
    if not path:
        print "ERR: %s has no path" % version
        return None
    app = DictObj()
    app.srcdir = path
    try:
        inv = fetch_inventory(app, path, object_file)
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
                url = "http://%s.readthedocs.org/en/latest/%s" % (
                    version.project.slug, url)
                save_term(version, term, url, title)
                if '.' in term:
                    save_term(version, term.split('.')[-1], url, title)
            except Exception, e: #Yes, I'm an evil person.
                print "*** Failed updating %s: %s" % (term, e)


def save_term(version, term, url, title):
    redis_obj = redis.Redis(**settings.REDIS)
    #print "Inserting %s: %s" % (term, url)
    lang = "en"
    project_slug = version.project.slug
    version_slug = version.slug
    redis_obj.sadd('redirects:v3:%s:%s:%s:%s' % (lang, project_slug,
                                         version_slug, term), url)
    redis_obj.setnx('redirects:v3:%s:%s:%s:%s:%s' % (lang, project_slug,
                                             version_slug, term, url), 1)


def symlink_cname(version):
    build_dir = version.project.rtd_build_path(version.slug)
    #Chop off the version from the end.
    build_dir = '/'.join(build_dir.split('/')[:-1])
    redis_conn = redis.Redis(**settings.REDIS)
    try:
        cnames = redis_conn.smembers('rtd_slug:v1:%s' % version.project.slug)
    except redis.ConnectionError:
        return
    for cname in cnames:
        print "Symlinking %s" % cname
        symlink = version.project.rtd_cname_path(cname)
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))
        run_on_app_servers('ln -nsf %s %s' % (build_dir, symlink))


def send_notifications(version):
    message = "Build of %s successful" % version
    redis_obj = redis.Redis(**settings.REDIS)
    IRC = getattr(settings, 'IRC_CHANNEL', '#readthedocs')
    redis_obj.publish('out',
                    json.dumps({
                    'version': 1,
                    'type': 'privmsg',
                    'data': {
                        'to': IRC,
                        'message': message,
                        }
                    }))
