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

from celery.decorators import task
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
import redis
import requests
import slumber
import tastyapi
from sphinx.ext import intersphinx

from builds.models import Build, Version
from doc_builder import loading as builder_loading
from doc_builder.base import restoring_chdir
from projects.exceptions import ProjectImportError
from projects.models import ImportedFile, Project
from projects.utils import (purge_version, run,
                            make_api_version, make_api_project)
from tastyapi import client as tastyapi_client
from tastyapi import api, apiv2
from core.utils import copy_to_app_servers, run_on_app_servers

ghetto_hack = re.compile(
    r'(?P<key>.*)\s*=\s*u?\[?[\'\"](?P<value>.*)[\'\"]\]?')

log = logging.getLogger(__name__)

LOG_TEMPLATE = u"(Build) [{project}:{version}] {msg}"
HTML_ONLY = getattr(settings, 'HTML_ONLY_PROJECTS', ())

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
def update_docs(pk, record=True, pdf=True, man=True, epub=True, dash=True,
                search=True, version_pk=None, force=False, intersphinx=True,
                api=None, **kwargs):
    """The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported or we
    created it.  Then it will build the html docs and other requested parts. It
    also handles clearing the varnish cache.

    `pk`
        Primary key of the project to update

    `record`
        Whether or not to keep a record of the update in the database. Useful
        for preventing changes visible to the end-user when running commands
        from the shell, for example.

    """

    if api is None:
        api = tastyapi.api

    project_data = api.project(pk).get()
    project = make_api_project(project_data)
    #if 'edx-platform' in  project.repo:
        # Skip edx for now
        #return

    log.info(LOG_TEMPLATE.format(project=project.slug, version='', msg='Building'))
    if version_pk:
        version_data = api.version(version_pk).get()
    else:
        branch = project.default_branch or project.vcs_repo().fallback_branch
        try:
            # Use latest version
            version_data = (api.version(project.slug)
                            .get(slug='latest')['objects'][0])
        except (slumber.exceptions.HttpClientError, IndexError):
            # Create the latest version since it doesn't exist
            version_data = dict(
                project='/api/v1/project/%s/' % project.pk,
                slug='latest',
                type='branch',
                active=True,
                verbose_name='latest',
                identifier=branch,
            )
            try:
                version_data = api.version.post(version_data)
            except Exception as e:
                log.info(LOG_TEMPLATE.format(project=project.slug, version='', msg='Exception in creating version: %s' % e))
                raise e

    version = make_api_version(version_data)

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
            version_data['project'] = ("/api/v1/version/%s/"
                                       % version_data['project'].pk)
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

    try:
        log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='Updating docs from VCS'))
        update_output = update_imported_docs(version.pk, api)
        #update_output = update_result.get()
    except ProjectImportError, err:
        log.error(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='Failed to import project; skipping build'), exc_info=True)
        build['state'] = 'finished'
        build['setup_error'] = (
            'Failed to import project; skipping build.\n'
            '\nError\n-----\n\n%s' % err.message
        )
        api.build(build['id']).put(build)
        return False

    ###
    # Keep state between the repo and the database
    ###
    log.debug(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='Setting config values from .rtd.yml'))
    try:
        update_config_from_json(version.pk)
    except Exception, e:
        # Never kill the build, but log the error
        log.error(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='Failure in config parsing code: %s ' % e.message))

    # kick off a build
    if record:
        # Update the build with info about the setup
        build['state'] = 'building'
        output_data = error_data = ''
        # Grab all the text from updating the code via VCS.
        for key in ['checkout', 'venv', 'sphinx', 'requirements', 'install']:
            data = update_output.get(key, None)
            if data:
                try:
                    output_data += u"\n\n%s\n\n%s\n\n" % (key.upper(), data[1])
                    error_data += u"\n\n%s\n\n%s\n\n" % (key.upper(), data[2])
                except UnicodeDecodeError:
                    log.debug(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Unicode Error in setup"))
        build['setup'] = output_data
        build['setup_error'] = error_data
        api.build(build['id']).put(build)

    log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Building docs"))
    # This is only checking the results of the HTML build, as it's a canary
    try:
        results = build_docs(version_pk=version.pk, pdf=pdf, man=man,
                             epub=epub, dash=dash, search=search,
                             record=record, force=force)
        (html_results, latex_results, pdf_results, man_results, epub_results,
         dash_results, search_results) = results
        (ret, out, err) = html_results
    except Exception as e:
        log.error(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Exception in flailboat build_docs"), exc_info=True)
        html_results = (999, "Project build Failed", str(e))
        latex_results = (999, "Project build Failed", str(e))
        pdf_results = (999, "Project build Failed", str(e))
        # These variables aren't currently being used.
        # man_results = (999, "Project build Failed", str(e))
        # epub_results = (999, "Project build Failed", str(e))
        # dash_results = (999, "Project build Failed", str(e))
        # search_results = (999, "Project build Failed", str(e))
        (ret, out, err) = html_results

    if record:
        # Update builds
        build['success'] = html_results[0] == 0
        build['output'] = html_results[1]
        build['error'] = html_results[2]
        build['state'] = 'finished'
        build['exit_code'] = html_results[0]
        api.build(build['id']).put(build)

        try:
            api.build.post(dict(
                project='/api/v1/project/%s/' % project.pk,
                version='/api/v1/version/%s/' % version.pk,
                success=pdf_results[0] == 0,
                type='pdf',
                setup=latex_results[1],
                setup_error=latex_results[2],
                output=pdf_results[1],
                error=pdf_results[2],
                exit_code=pdf_results[0],
            ))
        except UnicodeDecodeError, e:
            log.error(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Unable to post a new build"), exc_info=True)

    if version:
        # Mark version active on the site
        version_data = api.version(version.pk).get()
        version_data['active'] = True
        version_data['built'] = True
        # Need to delete this because a bug in tastypie breaks on the users
        # list.
        del version_data['project']
        try:
            api.version(version.pk).put(version_data)
        except Exception, e:
            log.error(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Unable to put a new version"), exc_info=True)

    # Build Finished, do house keeping bits

    if 'no targets are out of date.' in out:
        log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Build Unchanged"))
    else:
        if ret == 0:
            log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Successful Build"))
            purge_version(version, subdomain=True,
                          mainsite=True, cname=True)
            symlink_cnames(version)
            symlink_translations(version)
            symlink_subprojects(version)

            if project.single_version:
                symlink_single_version(version)
            else:
                remove_symlink_single_version(version)

            # This requires database access, must disable it for now.
            #send_notifications(version, build)
            #log.info("Purged %s" % version)
        else:
            log.warning(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Failed HTML Build"))

        # TODO: Find a better way to handle indexing.
        fileify.delay(version.pk)

        # Things that touch redis
        if intersphinx:
            update_intersphinx(version.pk, api)
        # Needs to happen after update_intersphinx
        #clear_artifacts(version.pk)

    import_open_comparison(project)
    import_crate(project)

    return True


def import_open_comparison(project):
    """
    Try importing a Project model from Open Comparison sites.
    """
    try:
        result = tastyapi_client.import_project(project)
        if result:
            log.debug(LOG_TEMPLATE.format(project=project.slug, version='', msg="Successful import from Open Comparison"))
        else:
            log.debug(LOG_TEMPLATE.format(project=project.slug, version='', msg="Failed import from Open Comparison"))
    except:
        log.debug("Failed import from Open Comparison", exc_info=True)


def import_crate(project):
    """
    Try importing a Project model from Crate.
    """
    try:
        result = tastyapi_client.import_crate(project)
        if result:
            log.debug(LOG_TEMPLATE.format(project=project.slug, version='', msg="Successful import from Crate"))
        else:
            log.debug(LOG_TEMPLATE.format(project=project.slug, version='', msg="Failed import from Crate"))
    except:
        log.debug(LOG_TEMPLATE.format(project=project.slug, version='', msg="Failed import from Crate"), exc_info=True)


@task 
def update_config_from_json(version_pk):
    """
    Check out or update the given project's repository.
    """
    # Remove circular import
    from projects.forms import ImportProjectForm
    version_data = api.version(version_pk).get()
    version = make_api_version(version_data)
    project = version.project
    log.debug(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Checking for json config"))
    try:
        rtd_json = open(os.path.join(
            project.checkout_path(version.slug),
            '.rtd.json'
        ))
        json_obj = json.load(rtd_json)
        for key in json_obj.keys():
            # Treat the defined fields on the Import form as 
            # the canonical list of allowed user editable fields.
            # This is in essense just another UI for that form.
            if key not in ImportProjectForm._meta.fields:
                del json_obj[key]
    except IOError:
        log.debug(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="No rtd.json found."))
        return None

    project_data = api.project(project.pk).get()
    project_data.update(json_obj)
    api.project(project.pk).put(project_data)
    log.debug(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Updated from JSON."))

@task
def update_imported_docs(version_pk, api=None):
    """
    Check out or update the given project's repository.
    """
    if api is None:
        api = tastyapi.api

    version_data = api.version(version_pk).get()
    version = make_api_version(version_data)
    project = version.project

    # Make Dirs
    if not os.path.exists(project.doc_path):
        os.makedirs(project.doc_path)

    with project.repo_lock(getattr(settings, 'REPO_LOCK_SECONDS', 30)):
        update_docs_output = {}
        if not project.vcs_repo():
            raise ProjectImportError(("Repo type '{0}' unknown"
                                      .format(project.repo_type)))

        # Get the actual code on disk
        if version:
            log.info(
                LOG_TEMPLATE.format(
                    project=project.slug, 
                    version=version.slug, 
                    msg='Checking out version {slug}: {identifier}'.format(
                        slug=version.slug, 
                        identifier=version.identifier
                    )
                )
            )
            version_slug = version.slug
            version_repo = project.vcs_repo(version_slug)
            update_docs_output['checkout'] = version_repo.checkout(
                version.identifier
            )
        else:
            # Does this ever get called?
            log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='Updating to latest revision'))
            version_slug = 'latest'
            version_repo = project.vcs_repo(version_slug)
            update_docs_output['checkout'] = version_repo.update()

        # Ensure we have a conf file (an exception is raised if not)
        try:
            project.conf_file(version.slug)
        except ProjectImportError:
            raise




        # Do Virtualenv bits:
        if project.use_virtualenv:
            build_dir = os.path.join(project.venv_path(version=version_slug), 'build')
            if os.path.exists(build_dir):
                log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='Removing existing build dir'))
                shutil.rmtree(build_dir)
            if project.use_system_packages:
                site_packages = '--system-site-packages'
            else:
                site_packages = '--no-site-packages'
            # Here the command has been modified to support different
            # interpreters.
            update_docs_output['venv'] = run(
                '{cmd} {site_packages} {path}'.format(
                    cmd='virtualenv-2.7 -p {interpreter}'.format(
                        interpreter=project.python_interpreter),
                    site_packages=site_packages,
                    path=project.venv_path(version=version_slug)
                )
            )
            # Other code expects sphinx-build to be installed inside the
            # virtualenv.  Using the -I option makes sure it gets installed
            # even if it is already installed system-wide (and
            # --system-site-packages is used)
            if project.use_system_packages:
                ignore_option = '-I'
            else:
                ignore_option = ''
            if project.python_interpreter != 'python3':
                sphinx = 'sphinx==1.2'
                update_docs_output['sphinx'] = run(
                    ('{cmd} install -U {ignore_option} {sphinx} '
                     'virtualenv==1.10.1 setuptools==1.1 '
                     'docutils==0.11 git+git://github.com/ericholscher/readthedocs-sphinx-ext#egg=readthedocs_ext').format(
                        cmd=project.venv_bin(version=version_slug, bin='pip'),
                        sphinx=sphinx, ignore_option=ignore_option))
            else:
                sphinx = 'sphinx==1.2'
                # python 3 specific hax
                update_docs_output['sphinx'] = run(
                    ('{cmd} install -U {ignore_option} {sphinx} '
                     'virtualenv==1.9.1 docutils==0.11 git+git://github.com/ericholscher/readthedocs-sphinx-ext#egg=readthedocs_ext').format(
                        cmd=project.venv_bin(version=version_slug, bin='pip'),
                        sphinx=sphinx, ignore_option=ignore_option))

            if project.requirements_file:
                os.chdir(project.checkout_path(version_slug))
                update_docs_output['requirements'] = run(
                    '{cmd} install --exists-action=w -r {requirements}'.format(
                        cmd=project.venv_bin(version=version_slug, bin='pip'),
                        requirements=project.requirements_file))
            os.chdir(project.checkout_path(version_slug))
            if os.path.isfile("setup.py"):
                if getattr(settings, 'USE_PIP_INSTALL', False):
                    update_docs_output['install'] = run(
                        '{cmd} install --ignore-installed .'.format(
                            cmd=project.venv_bin(version=version_slug, bin='pip')))
                else:
                    update_docs_output['install'] = run(
                        '{cmd} setup.py install --force'.format(
                            cmd=project.venv_bin(version=version_slug,
                                                 bin='python')))
            else:
                update_docs_output['install'] = (999, "", "No setup.py, skipping install")

        # Update tags/version

        version_post_data = {'repo': version_repo.repo_url}

        if version_repo.supports_tags:
            version_post_data['tags'] = [
                {'identifier': v.identifier,
                 'verbose_name': v.verbose_name,
                 } for v in version_repo.tags
            ]

        if version_repo.supports_branches:
            version_post_data['branches'] = [
                {'identifier': v.identifier,
                 'verbose_name': v.verbose_name,
                 } for v in version_repo.branches
            ]

        try:
            apiv2.project(project.pk).sync_versions.post(version_post_data)
        except Exception, e:
            print "Sync Verisons Exception: %s" % e.message

    return update_docs_output


@task
def build_docs(version_pk, pdf, man, epub, dash, search, record, force):
    """
    This handles the actual building of the documentation and DB records
    """
    version_data = api.version(version_pk).get()
    version = make_api_version(version_data)
    project = version.project

    if not project.conf_file(version.slug):
        return ('', 'Conf file not found.', -1)

    with project.repo_lock(getattr(settings, 'REPO_LOCK_SECONDS', 30)):

        html_builder = builder_loading.get(project.documentation_type)(version)
        if force:
            html_builder.force()
        html_builder.clean()
        html_results = html_builder.build()
        if html_results[0] == 0:
            html_builder.move()

        fake_results = (999, "Project Skipped, Didn't build",
                        "Project Skipped, Didn't build")
        # Only build everything else if the html build changed.
        if html_builder.changed and not project.skip:
            if search:
                try:
                    search_builder = builder_loading.get('sphinx_search')(version)
                    search_results = search_builder.build()
                    if search_results[0] == 0:
                        # Update search index
                        search_builder.upload()
                        # Copy json for safe keeping
                        search_builder.move()
                except:
                    log.error(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="JSON Build Error"), exc_info=True)
            if dash:
                dash_builder = builder_loading.get('sphinx_dash')(version)
                dash_results = dash_builder.build()
                if dash_results[0] == 0:
                    dash_builder.move()
            else:
                dash_results = fake_results

            if version.project.slug not in HTML_ONLY:
                if pdf:
                    pdf_builder = builder_loading.get('sphinx_pdf')(version)
                    latex_results, pdf_results = pdf_builder.build()
                    # Always move pdf results even when there's an error.
                    #if pdf_results[0] == 0:
                    pdf_builder.move()
                else:
                    pdf_results = latex_results = fake_results
                if man:
                    man_builder = builder_loading.get('sphinx_man')(version)
                    man_results = man_builder.build()
                    if man_results[0] == 0:
                        man_builder.move()
                else:
                    man_results = fake_results
                if epub:
                    epub_builder = builder_loading.get('sphinx_epub')(version)
                    epub_results = epub_builder.build()
                    if epub_results[0] == 0:
                        epub_builder.move()
                else:
                    epub_results = fake_results
            else:
                latex_results = pdf_results = man_results = epub_results = (999, "Optional builds disabled", "Optional builds disabled")


    return (html_results, latex_results, pdf_results, man_results,
            epub_results, dash_results, search_results)


@task
def fileify(version_pk):
    """
    Create ImportedFile objects for all of a version's files.

    This is a prereq for indexing the docs for search.
    It also causes celery-haystack to kick off an index of the file.
    """
    version_data = api.version(version_pk).get()
    version = make_api_version(version_data)
    project = version.project
    path = project.rtd_build_path(version.slug)
    log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='Indexing files'))
    if path:
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if fnmatch.fnmatch(filename, '*.html'):
                    dirpath = os.path.join(root.replace(path, '').lstrip('/'),
                                           filename.lstrip('/'))
                    if getattr(settings, 'DONT_HIT_DB', True):
                        api.file.post(dict(
                            project="/api/v1/project/%s/" % project.pk,
                            version="/api/v1/version/%s/" % version.pk,
                            path=dirpath,
                            name=filename))
                    else:
                        obj, created = ImportedFile.objects.get_or_create(
                            project=project,
                            version=version,
                            path=dirpath,
                            name=filename)
                        if not created:
                            obj.save()


#@periodic_task(run_every=crontab(hour="*", minute="*/5", day_of_week="*"))
def update_docs_pull(record=False, pdf=False, man=False, force=False):
    """
    A high-level interface that will update all of the projects.

    This is mainly used from a cronjob or management command.
    """
    for version in Version.objects.filter(built=True):
        try:
            update_docs(pk=version.project.pk, version_pk=version.pk,
                        record=record, pdf=pdf, man=man)
        except Exception:
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
def update_intersphinx(version_pk, api=None):
    if api is None:
        api = tastyapi.api

    version_data = api.version(version_pk).get()
    version = make_api_version(version_data)
    project = version.project

    try:
        object_file = version.project.find('objects.inv', version.slug)[0]
    except IndexError:
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
                                                     project_slug, term, url),
                    1)

def symlink_cnames(version):
    """
    OLD
    Link from HOME/user_builds/cnames/<cname> ->
              HOME/user_builds/<project>/rtd-builds/
    NEW
    Link from HOME/user_builds/cnametoproject/<cname> ->
              HOME/user_builds/<project>/
    """
    try:
        redis_conn = redis.Redis(**settings.REDIS)
        cnames = redis_conn.smembers('rtd_slug:v1:%s' % version.project.slug)
    except redis.ConnectionError:
        log.error(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg='Failed to symlink cnames, Redis error.'), exc_info=True)
        return
    for cname in cnames:
        log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg="Symlinking CNAME: %s" % cname))
        docs_dir = version.project.rtd_build_path(version.slug)
        # Chop off the version from the end.
        docs_dir = '/'.join(docs_dir.split('/')[:-1])
        # Old symlink location -- Keep this here til we change nginx over
        symlink = version.project.cnames_symlink_path(cname)
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))
        run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))
        # New symlink location 
        new_docs_dir = version.project.doc_path
        new_cname_symlink = os.path.join(getattr(settings, 'SITE_ROOT'), 'cnametoproject', cname)
        run_on_app_servers('mkdir -p %s' % '/'.join(new_cname_symlink.split('/')[:-1]))
        run_on_app_servers('ln -nsf %s %s' % (new_docs_dir, new_cname_symlink))


def symlink_subprojects(version):
    """
    Link from HOME/user_builds/project/subprojects/<project> ->
              HOME/user_builds/<project>/rtd-builds/
    """
    # Subprojects
    subprojects = apiv2.project(version.project.pk).subprojects.get()['subprojects']
    for subproject_data in subprojects:
        subproject_slug = subproject_data['slug']
        log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg="Symlinking subproject: %s" % subproject_slug))

        # The directory for this specific subproject
        symlink = version.project.subprojects_symlink_path(subproject_slug)
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))

        # Where the actual docs live
        docs_dir = os.path.join(settings.DOCROOT, subproject_slug, 'rtd-builds')
        run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))


def symlink_translations(version):
    """
    Link from HOME/user_builds/project/translations/<lang> ->
              HOME/user_builds/<project>/rtd-builds/
    """
    translations = apiv2.project(version.project.pk).translations.get()['translations']
    for translation_data in translations:
        translation_slug = translation_data['slug']
        translation_language = translation_data['language']
        log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg="Symlinking translation: %s->%s" % (translation_language, translation_slug)))

        # The directory for this specific translation
        symlink = version.project.translations_symlink_path(translation_language)
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))

        # Where the actual docs live
        docs_dir = os.path.join(settings.DOCROOT, translation_slug, 'rtd-builds')
        run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))

    # Hack in the en version for backwards compat
    symlink = version.project.translations_symlink_path('en')
    run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))
    docs_dir = os.path.join(version.project.doc_path, 'rtd-builds')
    run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))
    # Add the main language project to nginx too
    if version.project.language is not 'en':
        symlink = version.project.translations_symlink_path(version.project.language)
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))
        docs_dir = os.path.join(settings.DOCROOT, version.project.slug, 'rtd-builds')
        run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))

def symlink_single_version(version):
    """
    Link from HOME/user_builds/<project>/single_version ->
              HOME/user_builds/<project>/rtd-builds/<default_version>/
    """
    default_version = version.project.default_version
    log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=default_version, msg="Symlinking single_version"))

    # The single_version directory
    symlink = version.project.single_version_symlink_path()
    run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))

    # Where the actual docs live
    docs_dir = os.path.join(settings.DOCROOT, version.project.slug, 'rtd-builds', default_version)
    run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))

def remove_symlink_single_version(version):
    """Remove single_version symlink"""
    log.debug(LOG_TEMPLATE.format(
        project=version.project.slug,
        version=version.project.default_version,
        msg="Removing symlink for single_version")
    )
    symlink = version.project.single_version_symlink_path()
    run_on_app_servers('rm %s' % symlink)

def send_notifications(version, build):
    #zenircbot_notification(version.id)
    for hook in version.project.webhook_notifications.all():
        webhook_notification.delay(version.project.id, build, hook.url)
    emails = (version.project.emailhook_notifications.all()
              .values_list('email', flat=True))
    for email in emails:
        email_notification(version.project.id, build, email)


@task
def email_notification(project_id, build, email):
    if build['success']:
        return
    project = Project.objects.get(id=project_id)
    build_obj = Build.objects.get(id=build['id'])
    subject = (_('(ReadTheDocs) Building docs for %s failed') % project.name)
    template = 'projects/notification_email.txt'
    context = {
        'project': project.name,
        'build_url': 'http://%s%s' % (Site.objects.get_current().domain,
                                      build_obj.get_absolute_url())
    }
    message = get_template(template).render(Context(context))

    send_mail(subject=subject, message=message,
              from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=(email,))


@task
def webhook_notification(project_id, build, hook_url):
    project = Project.objects.get(id=project_id)
    data = json.dumps({
        'name': project.name,
        'slug': project.slug,
        'build': {
            'id': build['id'],
            'success': build['success'],
            'date': build['date']
        }
    })
    log.debug(LOG_TEMPLATE.format(project=project.slug, version='', msg='sending notification to: %s' % hook_url))
    requests.post(hook_url, data=data)


@task
def zenircbot_notification(version_id):
    version = Version.objects.get(id=version_id)
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


@task
def clear_artifacts(version_pk):
    """ Remove artifacts from the build server. """
    # Stop doing this for now as it causes 403s if people build things back to
    # back some times because of a race condition
    #version_data = api.version(version_pk).get()
    #version = make_api_version(version_data)
    #run('rm -rf %s' % version.project.full_epub_path(version.slug))
    #run('rm -rf %s' % version.project.full_man_path(version.slug))
    #run('rm -rf %s' % version.project.full_build_path(version.slug))
    #run('rm -rf %s' % version.project.full_latex_path(version.slug))
