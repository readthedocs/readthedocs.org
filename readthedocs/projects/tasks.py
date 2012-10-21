"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""
import fnmatch
import os
import re
import shutil
import json
import logging
import operator

from celery.decorators import task, periodic_task
from celery.task.schedules import crontab
from django.db import transaction
from django.conf import settings
import redis
from sphinx.ext import intersphinx
import slumber


from builds.models import Version
from doc_builder import loading as builder_loading
from doc_builder.base import restoring_chdir
from projects.exceptions import ProjectImportError
from projects.models import ImportedFile, Project
from projects.utils import (
    mkversion,
    purge_version,
    run,
    slugify_uniquely,
    make_api_version,
    make_api_project,
    )
from tastyapi import client as tastyapi_client
from tastyapi import api
from core.utils import copy_to_app_servers, run_on_app_servers

ghetto_hack = re.compile(
    r'(?P<key>.*)\s*=\s*u?\[?[\'\"](?P<value>.*)[\'\"]\]?')

log = logging.getLogger(__name__)

@task
def remove_dir(path):
    """
    Remove a directory on the build/celery server.

    This is mainly a wrapper around shutil.rmtree so that app servers
    can kill things on the build server.
    """
    log.info("Removing %s" % path)
    shutil.rmtree(path)


@task
@restoring_chdir
def update_docs(pk, record=True, pdf=True, man=True, epub=True, version_pk=None, force=False, **kwargs):
    """
    The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported or we created it.
    Then it will build the html docs and other requested parts.
    It also handles clearing the varnish cache.

    `pk`
        Primary key of the project to update

    `record`
        Whether or not to keep a record of the update in the database. Useful
        for preventing changes visible to the end-user when running commands from
        the shell, for example.
    """

    ###
    # Handle passed in arguments
    ###
    project_data = api.project(pk).get()
    project = make_api_project(project_data)

    # Prevent saving the temporary Project instance
    def new_save(*args, **kwargs):
        log.warning("Called save on a non-real object.")
        return 0
    project.save = new_save

    log.info("Building %s" % project)
    if version_pk:
        version_data = api.version(version_pk).get()
    else:
        branch = project.default_branch or project.vcs_repo().fallback_branch
        try:
            # Use latest version
            version_data = api.version(project.slug).get(slug='latest')['objects'][0]
        except (slumber.exceptions.HttpClientError, IndexError):
            # Create the latest version since it doesn't exist
            version_data = dict(
                project='/api/v1/project/%s/' % project.pk,
                slug='latest',
                active=True,
                verbose_name='latest',
                identifier=branch,
                )
            try:
                version_data = api.version.post(version_data)
            except Exception as e:
                log.info("Exception in creating version: %s" % e)
                raise e

    version = make_api_version(version_data)
    version.save = new_save

    if not version_pk:
        # Lots of course correction.
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
            version_data['project'] = "/api/v1/version/%s/" % version_data['project'].pk
            api.version(version.pk).put(version_data)

    if record:
        # Create Build Object.
        build = api.build.post(dict(
            project='/api/v1/project/%s/' % project.pk,
            version='/api/v1/version/%s/' % version.pk,
            type='html',
            state='triggered',
        ))
    else:
        build = {}

    # Make Dirs
    if not os.path.exists(project.doc_path):
        os.makedirs(project.doc_path)
    with project.repo_lock(getattr(settings, 'REPO_LOCK_SECONDS', 30)):
        try:
            update_output = update_imported_docs.apply_sync(args=[project.pk, version.pk], queue='syncer')
        except ProjectImportError, err:
            log.error("Failed to import project; skipping build.", exc_info=True)
            build['state'] = 'finished'
            build['setup_error'] = 'Failed to import project; skipping build.\nPlease make sure your repo is correct and you have a conf.py'
            api.build(build['id']).put(build)
            return False

        # kick off a build
        if record:
            # Update the build with info about the setup
            build['state'] = 'building'
            output_data = error_data = ''
            # Grab all the text from updating the code via VCS.
            for key in ['checkout', 'venv', 'sphinx', 'requirements', 'install']:
                data = update_output.get(key, None)
                if data:
                    output_data += u"\n\n%s\n\n%s\n\n" % (key.upper(), data[1])
                    error_data += u"\n\n%s\n\n%s\n\n" % (key.upper(), data[2])
            build['setup'] = output_data
            build['setup_error'] = error_data
            api.build(build['id']).put(build)
       
        # This is only checking the results of the HTML build, as it's a canary
        (html_results, pdf_results, man_results, epub_results) = build_docs.apply_async(
            kwargs=dict(
                project=project, version=version, build=build, pdf=pdf, man=man,
                epub=epub, record=record, force=force
                ),
            queue='syncer'
        )

        if record:
            #Update build.
            api.build.post(dict(
                project = '/api/v1/project/%s/' % project.pk,
                version = '/api/v1/version/%s/' % version.pk,
                success = html_results[0] == 0,
                output = out[1],
                error = out[2],
                state = 'finished',
            ))
            api.build.post(dict(
                project = '/api/v1/project/%s/' % project.pk,
                version = '/api/v1/version/%s/' % version.pk,
                success=pdf_results[0] == 0,
                type='pdf',
                setup=latex_results[1],
                setup_error=latex_results[2],
                output=pdf_results[1],
                error=pdf_results[2],
            ))
        if version:
            # Mark version active on the site
            version_data = api.version(version.pk).get()
            version_data['active'] = True
            version_data['built'] = True
            #Need to delete this because a bug in tastypie breaks on the users list.
            del version_data['project']
            try:
                api.version(version.pk).put(version_data)
            except Exception, e:
                log.error("Unable to post a new version", exc_info=True)


        if 'no targets are out of date.' in out:
            log.info("Build Unchanged")
        else:
            if ret == 0:
                log.info("Successful HTML Build")
                purge_version(version, subdomain=True,
                              mainsite=True, cname=True)
                symlink_cname(version)
                update_intersphinx(version.pk)
                send_notifications(version)
                log.info("Purged %s" % version)
            else:
                log.warning("Failed HTML Build")

        # Needs to happen every build
        clear_artifacts(version)

    # Try importing from Open Comparison sites.
    try:
        result = tastyapi_client.import_project(project)
        if result:
            log.info("Successful import from Open Comparison")
        else:
            log.info("Failed import from Open Comparison")
    except:
        log.info("Failed import from Open Comparison", exc_info=True)

    # Try importing from Crate
    try:
        result = tastyapi_client.import_crate(project)
        if result:
            log.info("Successful import from Crate")
        else:
            log.info("Failed import from Crate")

    except:
        log.info("Failed import from Crate", exc_info=True)

    return True

@task
def update_imported_docs(project, version):
    """
    Check out or update the given project's repository.
    """
    update_docs_output = {}
    if not project.vcs_repo():
        raise ProjectImportError("Repo type '{repo_type}' unknown".format(
                repo_type=project.repo_type))

    # Get the actual code on disk
    if version:
        log.info('Checking out version {slug}: {identifier}'.format(
            slug=version.slug, identifier=version.identifier))
        version_slug = version.slug
        version_repo = project.vcs_repo(version_slug)
        update_docs_output['checkout'] = version_repo.checkout(version.identifier)
    else:
        # Does this ever get called?
        log.info('Updating to latest revision')
        version_slug = 'latest'
        version_repo = project.vcs_repo(version_slug)
        update_docs_output['checkout'] = version_repo.update()

    # Ensure we have a conf file (an exception is raised if not)
    project.conf_file(version.slug)

    # Do Virtualenv bits:
    if project.use_virtualenv:
        if project.use_system_packages:
            site_packages = '--system-site-packages'
        else:
            site_packages = '--no-site-packages'
        update_docs_output['venv'] = run('{cmd} --distribute {site_packages} {path}'.format(
                cmd='virtualenv',
                site_packages=site_packages,
                path=project.venv_path(version=version_slug)))
        # Other code expects sphinx-build to be installed inside the virtualenv.
        # Using the -I option makes sure it gets installed even if it is
        # already installed system-wide (and --system-site-packages is used)
        if project.use_system_packages:
            ignore_option = '-I'
        else:
            ignore_option = ''
        update_docs_output['sphinx'] = run('{cmd} install -U {ignore_option} hg+http://bitbucket.org/birkenfeld/sphinx/@d4c6ac1fcc9c#egg=Sphinx virtualenv==1.8.2 distribute==0.6.28 docutils==0.8.1'.format(
                cmd=project.venv_bin(version=version_slug, bin='pip'), ignore_option=ignore_option))

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
        old_versions = [obj['identifier'] for obj in api.version.get(project__slug=project.slug, limit=500)['objects']]
        if version_repo.supports_tags:
            transaction.enter_transaction_management(True)
            tags = version_repo.tags
            for tag in tags:
                if tag.identifier in old_versions:
                    continue
                log.debug('NEW TAG: (%s not in %s)' % (tag.identifier, old_versions))
                slug = slugify_uniquely(Version, tag.verbose_name,
                                        'slug', 255, project=project)
                try:

                    version_data = api.version.post(dict(
                        project="/api/v1/project/%s/" % project.pk,
                        slug=slug,
                        identifier=tag.identifier,
                        verbose_name=tag.verbose_name
                    ))
                    ver = make_api_version(version_data)
                    log.info("New tag found: {0}".format(tag.identifier))
                    ver, highest = project.highest_version[1]
                    ver_obj = mkversion(ver)
                    #TODO: Handle updating higher versions automatically.
                    #This never worked very well, anyways.
                    if highest and ver_obj and ver_obj > highest:
                        log.info("Highest version known, building docs")
                        update_docs.delay(ver.project.pk, version_pk=ver.pk)
                except Exception, e:
                    log.error("Failed to create version (tag)", exc_info=True)
                    transaction.rollback()
            transaction.leave_transaction_management()
        if version_repo.supports_branches:
            transaction.enter_transaction_management(True)
            branches = version_repo.branches
            for branch in branches:
                if branch.identifier in old_versions:
                    continue
                log.debug('NEW BRANCH: (%s not in %s)' % (branch, old_versions))
                slug = slugify_uniquely(Version, branch.verbose_name,
                                        'slug', 255, project=project)
                try:
                    api.version.post(dict(
                        project="/api/v1/project/%s/" % project.pk,
                        slug=slug,
                        identifier=branch.identifier,
                        verbose_name=branch.verbose_name
                    ))
                    log.info("New branch found: {0}".format(branch.identifier))
                except Exception, e:
                    log.error("Failed to create version (branch)", exc_info=True)
                    transaction.rollback()
            transaction.leave_transaction_management()
            #TODO: Kill deleted branches
    except ValueError, e:
        log.error("Error getting tags", exc_info=True)

    #TODO: Find a better way to handle indexing.
    #fileify(version)
    return update_docs_output

@task
def build_docs(project, build, version, pdf, man, epub, record, force):
    """
    This handles the actual building of the documentation and DB records
    """
    if not project.conf_file(version.slug):
        return ('', 'Conf file not found.', -1)

    html_builder = builder_loading.get(project.documentation_type)(version)
    if force:
        html_builder.force()
    html_builder.clean()
    if record:
        html_results = html_builder.build(id=build['id'])
    else:
        html_results = html_builder.build()
    if html_results[0] == 0:
        html_builder.move()

    # Only build everything else if the html build changed.
    if html_builder.changed:
        if pdf and not project.skip:
            pdf_builder = builder_loading.get('sphinx_pdf')(version)
            latex_results, pdf_results = pdf_builder.build()
            pdf_builder.move()
        if man and not project.skip:
            man_builder = builder_loading.get('sphinx_man')(version)
            man_results = man_builder.build()
            man_builder.move()
        if epub and not project.skip:
            epub_builder = builder_loading.get('sphinx_epub')(version)
            epub_results = epub_builder.build()
            epub_builder.move()

    return (html_results, pdf_results, man_results, epub_results)


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
                    if getattr(settings, 'DONT_HIT_DB', True):
                        api.file.post(dict(
                            project="/api/v1/project/%s/" % project.pk,
                            path=dirpath,
                            name=filename))
                    else:
                        ImportedFile.objects.get_or_create(
                            project=project,
                            path=dirpath,
                            name=filename)


#@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def update_docs_pull(record=False, pdf=False, man=False, force=False):
    """
    A high-level interface that will update all of the projects.

    This is mainly used from a cronjob or management command.
    """
    for version in Version.objects.filter(built=True):
        try:
            update_docs(
                pk=version.project.pk, version_pk=version.pk, record=record, pdf=pdf, man=man)
        except Exception, e:
            log.error("update_docs_pull failed", exc_info=True)


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
    version = make_api_version(version_data)
    project = version.project

    try:
        object_file = version.project.find('objects.inv', version.slug)[0]
    except IndexError, e:
        print "Failed to find objects file"
        return None

    f = open(object_file)
    f.readline()
    urlpattern = "http://%s/en/%s/%%s" % (project.subdomain, version.slug)
    data = intersphinx.read_inventory_v2(f, urlpattern, operator.mod)
    for top_key in data.keys():
        #print "KEY: %s" % top_key
        inner_keys = data[top_key].keys()
        for inner_key in inner_keys:
            #print "INNER KEY: %s" % inner_key
            _project, sphinx_version, url, title = data[top_key][inner_key]
            try:
                url_key = url.split('#')[1]
            except IndexError:
                # Invalid data
                continue
            if ":" in url_key:
                #This dumps junk data into the url namespace we don't need
                #print "INNER: %s->%s" % (inner_key, url)
                save_term(version, inner_key, url)
            else:
                last_key = url_key.split('.')[-1]
                if last_key != url_key:
                    #Only save last key if it differes
                    #print "LAST: %s->%s" % (last_key, url)
                    save_term(version, last_key, url)
                #print "URL: %s->%s" % (url_key, url)
                save_term(version, url_key, url)

def save_term(version, term, url):
    redis_obj = redis.Redis(**settings.REDIS)
    lang = "en"
    project_slug = version.project.slug
    version_slug = version.slug
    redis_obj.sadd('redirects:v4:%s:%s:%s:%s' % (lang, version_slug,
                                         project_slug, term), url)
    redis_obj.setnx('redirects:v4:%s:%s:%s:%s:%s' % (lang, version_slug,
                                             project_slug, term, url), 1)


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
        log.info("Symlinking %s" % cname)
        symlink = version.project.rtd_cname_path(cname)
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))
        run_on_app_servers('ln -nsf %s %s' % (build_dir, symlink))


def send_notifications(version):
    message = "Build of %s successful" % version
    redis_obj = redis.Redis(**settings.REDIS)
    IRC = getattr(settings, 'IRC_CHANNEL', '#readthedocs-build')
    try:
        redis_obj.publish('out',
                        json.dumps({
                        'version': 1,
                        'type': 'privmsg',
                        'data': {
                            'to': IRC,
                            'message': message,
                            }
                        }))
    except redis.ConnectionError:
        return

def clear_artifacts(version):
    """ Remove artifacts from the build server. """
    run('rm -rf %s' % version.project.full_build_path(version.slug))
    run('rm -rf %s' % version.project.full_latex_path(version.slug))
    run('rm -rf %s' % version.project.full_epub_path(version.slug))
    run('rm -rf %s' % version.project.full_man_path(version.slug))
