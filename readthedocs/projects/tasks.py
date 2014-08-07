"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""
import fnmatch
import os
import shutil
import json
import logging
import uuid

from celery import task
from django.conf import settings
import redis
import slumber
import tastyapi

from builds.models import Build, Version
from doc_builder import loading as builder_loading
from doc_builder.base import restoring_chdir
from projects.exceptions import ProjectImportError
from projects.models import ImportedFile, Project
from projects.utils import (purge_version, run,
                            make_api_version, make_api_project)
from projects.constants import LOG_TEMPLATE
from projects import symlinks
from tastyapi import api, apiv2
from core.utils import (copy_to_app_servers, copy_file_to_app_servers,
                        run_on_app_servers)
from core import utils as core_utils
from search.parse_json import process_all_json_files
from vcs_support import utils as vcs_support_utils

log = logging.getLogger(__name__)

HTML_ONLY = getattr(settings, 'HTML_ONLY_PROJECTS', ())


@task(default_retry_delay=7 * 60, max_retries=5)
@restoring_chdir
def update_docs(pk, version_pk=None, record=True, docker=False,
                pdf=True, man=True, epub=True, dash=True,
                search=True, force=False, intersphinx=True, localmedia=True,
                api=None, **kwargs):
    """
    The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported or we
    created it.  Then it will build the html docs and other requested parts.

    `pk`
        Primary key of the project to update

    `record`
        Whether or not to keep a record of the update in the database. Useful
        for preventing changes visible to the end-user when running commands
        from the shell, for example.

    """

    # Dependency injection to allow for testing
    if api is None:
        api = tastyapi.api

    project_data = api.project(pk).get()
    project = make_api_project(project_data)
    log.info(LOG_TEMPLATE.format(
        project=project.slug, version='', msg='Building'))
    version = ensure_version(api, project, version_pk)
    build = create_build(version, api, record)
    results = {}

    try:
        record_build(
            api=api, build=build, record=record, results=results, state='cloning')
        vcs_results = setup_vcs(version, build, api)
        if vcs_results:
            results.update(vcs_results)

        if docker:
            record_build(
                api=api, build=build, record=record, results=results, state='building')
            build_results = run_docker(version)
            results.update(build_results)
        else:
            record_build(
                api=api, build=build, record=record, results=results, state='installing')
            setup_results = setup_environment(version)
            results.update(setup_results)

            record_build(
                api=api, build=build, record=record, results=results, state='building')
            build_results = build_docs(
                version, force, pdf, man, epub, dash, search, localmedia)
            results.update(build_results)

        move_files(version, results)
        record_pdf(api=api, record=record, results=results,
                   state='finished', version=version)
        finish_build(version=version, build=build, results=results)

        if results['html'][0] == 0:
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
                log.error(LOG_TEMPLATE.format(project=version.project.slug,
                                              version=version.slug, msg="Unable to put a new version"), exc_info=True)
    except vcs_support_utils.LockTimeout, e:
        results['checkout'] = (
            999, "", "Version locked, retrying in 5 minutes.")
        log.info(LOG_TEMPLATE.format(project=version.project.slug,
                                     version=version.slug, msg="Unable to lock, will retry"))
        # http://celery.readthedocs.org/en/3.0/userguide/tasks.html#retrying
        # Should completely retry the task for us until max_retries is exceeded
        update_docs.retry(exc=e, throw=False)
    except Exception, e:
        log.error(LOG_TEMPLATE.format(project=version.project.slug,
                                      version=version.slug, msg="Top-level Build Failure"), exc_info=True)
    finally:
        record_build(
            api=api, build=build, record=record, results=results, state='finished')
        log.info(LOG_TEMPLATE.format(
            project=version.project.slug, version='', msg='Build finished'))


def move_files(version, results):
    if results['html'][0] == 0:
        from_path = version.project.artifact_path(
            version=version.slug, type=version.project.documentation_type)
        target = version.project.rtd_build_path(version.slug)
        core_utils.copy(from_path, target)

    if 'sphinx' in version.project.documentation_type:
        if 'localmedia' in results and results['localmedia'][0] == 0:
            from_path = version.project.artifact_path(
                version=version.slug, type='sphinx_localmedia')
            to_path = os.path.join(
                settings.MEDIA_ROOT, 'htmlzip', version.project.slug, version.slug)
            core_utils.copy(from_path, to_path)
        if 'search' in results and results['search'][0] == 0:
            from_path = version.project.artifact_path(
                version=version.slug, type='sphinx_search')
            to_path = os.path.join(
                settings.MEDIA_ROOT, 'json', version.project.slug, version.slug)
            core_utils.copy(from_path, to_path)
        # Always move PDF's because the return code lies.
        if 'pdf' in results:
            try:
                from_path = version.project.artifact_path(
                    version=version.slug, type='sphinx_pdf')
                to_path = os.path.join(
                    settings.MEDIA_ROOT, 'pdf', version.project.slug, version.slug)
                core_utils.copy(from_path, to_path)
            except:
                pass
        if 'epub' in results and results['epub'][0] == 0:
            from_path = version.project.artifact_path(
                version=version.slug, type='sphinx_epub')
            to_path = os.path.join(
                settings.MEDIA_ROOT, 'epub', version.project.slug, version.slug)
            core_utils.copy(from_path, to_path)


def run_docker(version):
    serialized_path = os.path.join(version.project.doc_path, 'build.json')
    if os.path.exists(serialized_path):
        os.remove(serialized_path)
    path = version.project.doc_path
    docker_results = run('docker run -v %s:/home/docs/checkouts/readthedocs.org/user_builds/%s ericholscher/readthedocs-build /bin/bash /home/docs/run.sh %s' %
                         (path, version.project.slug, version.project.slug))
    path = os.path.join(version.project.doc_path, 'build.json')
    if os.path.exists(path):
        json_file = open(path)
        serialized_results = json.load(json_file)
        json_file.close()
    else:
        serialized_results = {}
    return serialized_results


def docker_build(version_pk, pdf=True, man=True, epub=True, dash=True, search=True, force=False, intersphinx=True, localmedia=True):
    """
    The code that executes inside of docker
    """
    version_data = api.version(version_pk).get()
    version = make_api_version(version_data)

    environment_results = setup_environment(version)
    results = build_docs(version=version, force=force, pdf=pdf, man=man,
                         epub=epub, dash=dash, search=search, localmedia=localmedia)
    results.update(environment_results)
    try:
        number = uuid.uuid4()
        path = os.path.join(version.project.doc_path, 'build.json')
        fh = open(path, 'w')
        json.dump(results, fh)
        fh.close()
    except IOError as e:
        log.debug(LOG_TEMPLATE.format(
            project=version.project.slug,
            version='',
            msg='Cannot write to build.json: {0}'.format(e)
        ))
        return None
    return number


def ensure_version(api, project, version_pk):
    """
    Ensure we're using a sane version.
    This also creates the "latest" version if it doesn't exist.
    """

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
                log.info(LOG_TEMPLATE.format(
                    project=project.slug, version='', msg='Exception in creating version: %s' % e))
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
            version_data['project'] = ("/api/v1/project/%s/"
                                       % version_data['project'].pk)
            api.version(version.pk).put(version_data)

    return version


def setup_vcs(version, build, api):
    """
    Update the checkout of the repo to make sure it's the latest.
    This also syncs versions in the DB.
    """

    log.info(LOG_TEMPLATE.format(project=version.project.slug,
                                 version=version.slug, msg='Updating docs from VCS'))
    try:
        update_output = update_imported_docs(version.pk, api)
        commit = version.project.vcs_repo(version.slug).commit
        if commit:
            build['commit'] = commit
    except ProjectImportError, err:
        log.error(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug,
                                      msg='Failed to import project; skipping build'), exc_info=True)
        build['state'] = 'finished'
        build['setup_error'] = (
            'Failed to import project; skipping build.\n'
            '\nError\n-----\n\n%s' % err.message
        )
        api.build(build['id']).put(build)
        return False
    return update_output


@task()
def update_imported_docs(version_pk, api=None):
    """
    Check out or update the given project's repository.
    """
    if api is None:
        api = tastyapi.api

    version_data = api.version(version_pk).get()
    version = make_api_version(version_data)
    project = version.project
    ret_dict = {}

    # Make Dirs
    if not os.path.exists(project.doc_path):
        os.makedirs(project.doc_path)

    with project.repo_nonblockinglock(version=version,
                                      max_lock_age=getattr(settings, 'REPO_LOCK_SECONDS', 30)):
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
            ret_dict['checkout'] = version_repo.checkout(
                version.identifier
            )
        else:
            # Does this ever get called?
            log.info(LOG_TEMPLATE.format(
                project=project.slug, version=version.slug, msg='Updating to latest revision'))
            version_slug = 'latest'
            version_repo = project.vcs_repo(version_slug)
            ret_dict['checkout'] = version_repo.update()

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
    return ret_dict


def setup_environment(version):
    """
    Build the virtualenv and install the project into it.
    """
    ret_dict = {}
    project = version.project
    if project.use_virtualenv:
        build_dir = os.path.join(
            project.venv_path(version=version.slug), 'build')
        if os.path.exists(build_dir):
            log.info(LOG_TEMPLATE.format(
                project=project.slug, version=version.slug, msg='Removing existing build dir'))
            shutil.rmtree(build_dir)
        if project.use_system_packages:
            site_packages = '--system-site-packages'
        else:
            site_packages = '--no-site-packages'
        # Here the command has been modified to support different
        # interpreters.
        ret_dict['venv'] = run(
            '{cmd} {site_packages} {path}'.format(
                cmd='virtualenv-2.7 -p {interpreter}'.format(
                    interpreter=project.python_interpreter),
                site_packages=site_packages,
                path=project.venv_path(version=version.slug)
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
        sphinx = 'sphinx==1.2.2'
        if project.python_interpreter != 'python3':
            ret_dict['sphinx'] = run(
                ('{cmd} install -U {ignore_option} {sphinx} '
                 'virtualenv==1.10.1 setuptools==1.1 '
                 'docutils==0.11 git+git://github.com/ericholscher/readthedocs-sphinx-ext#egg=readthedocs_ext').format(
                    cmd=project.venv_bin(version=version.slug, bin='pip'),
                    sphinx=sphinx, ignore_option=ignore_option))
        else:
            # python 3 specific hax
            ret_dict['sphinx'] = run(
                ('{cmd} install -U {ignore_option} {sphinx} '
                 'virtualenv==1.9.1 docutils==0.11 git+git://github.com/ericholscher/readthedocs-sphinx-ext#egg=readthedocs_ext').format(
                    cmd=project.venv_bin(version=version.slug, bin='pip'),
                    sphinx=sphinx, ignore_option=ignore_option))

        if project.requirements_file:
            os.chdir(project.checkout_path(version.slug))
            ret_dict['requirements'] = run(
                '{cmd} install --exists-action=w -r {requirements}'.format(
                    cmd=project.venv_bin(version=version.slug, bin='pip'),
                    requirements=project.requirements_file))
        os.chdir(project.checkout_path(version.slug))
        if os.path.isfile("setup.py"):
            if getattr(settings, 'USE_PIP_INSTALL', False):
                ret_dict['install'] = run(
                    '{cmd} install --ignore-installed .'.format(
                        cmd=project.venv_bin(version=version.slug, bin='pip')))
            else:
                ret_dict['install'] = run(
                    '{cmd} setup.py install --force'.format(
                        cmd=project.venv_bin(version=version.slug,
                                             bin='python')))
        else:
            ret_dict['install'] = (999, "", "No setup.py, skipping install")
    return ret_dict


@task()
def build_docs(version, force, pdf, man, epub, dash, search, localmedia):
    """
    This handles the actual building of the documentation
    """

    project = version.project
    results = {}

    if 'sphinx' in project.documentation_type:
        try:
            project.conf_file(version.slug)
        except ProjectImportError:
            results['html'] = (999, 'Conf file not found.', '')
            return results

    with project.repo_nonblockinglock(version=version,
                                      max_lock_age=getattr(settings, 'REPO_LOCK_SECONDS', 30)):
        html_builder = builder_loading.get(project.documentation_type)(version)
        if force:
            html_builder.force()
        # html_builder.clean()
        if 'sphinx' in project.documentation_type:
            html_builder.append_conf()
        results['html'] = html_builder.build()
        if results['html'][0] == 0:
            html_builder.move()

        fake_results = (999, "Project Skipped, Didn't build",
                        "Project Skipped, Didn't build")
        if 'sphinx' in project.documentation_type:
            # Search builder. Creates JSON from docs and sends it to the
            # server.
            if search:
                try:
                    search_builder = builder_loading.get(
                        'sphinx_search')(version)
                    results['search'] = search_builder.build()
                    if results['search'][0] == 0:
                        # Copy json for safe keeping
                        search_builder.move()
                except:
                    log.error(LOG_TEMPLATE.format(
                        project=project.slug, version=version.slug, msg="JSON Build Error"), exc_info=True)
            # Local media builder for singlepage HTML download archive
            if localmedia:
                try:
                    localmedia_builder = builder_loading.get(
                        'sphinx_singlehtmllocalmedia')(version)
                    results['localmedia'] = localmedia_builder.build()
                    if results['localmedia'][0] == 0:
                        localmedia_builder.move()
                except:
                    log.error(LOG_TEMPLATE.format(
                        project=project.slug, version=version.slug, msg="Local Media HTML Build Error"), exc_info=True)

            # Optional build steps
            if version.project.slug not in HTML_ONLY and not project.skip:
                if pdf:
                    pdf_builder = builder_loading.get('sphinx_pdf')(version)
                    results['pdf'] = pdf_builder.build()
                    # Always move pdf results even when there's an error.
                    # if pdf_results[0] == 0:
                    pdf_builder.move()
                else:
                    results['pdf'] = fake_results
                if epub:
                    epub_builder = builder_loading.get('sphinx_epub')(version)
                    results['epub'] = epub_builder.build()
                    if results['epub'][0] == 0:
                        epub_builder.move()
                else:
                    results['epub'] = fake_results
    return results


def finish_build(version, build, results):
    """
    Build Finished, do house keeping bits
    """

    (ret, out, err) = results['html']

    if 'no targets are out of date.' in out:
        log.info(LOG_TEMPLATE.format(
            project=version.project.slug, version=version.slug, msg="Build Unchanged"))
    else:
        if ret == 0:
            log.info(LOG_TEMPLATE.format(
                project=version.project.slug, version=version.slug, msg="Successful Build"))
            update_search(version)
            # fileify.delay(version.pk)
            symlinks.symlink_cnames(version)
            symlinks.symlink_translations(version)
            symlinks.symlink_subprojects(version)

            try:
                update_static_metadata(version.project.pk)
            except Exception:
                log.error("Unable to post a new build", exc_info=True)

            if version.project.single_version:
                symlinks.symlink_single_version(version)
            else:
                symlinks.remove_symlink_single_version(version)

            # This requires database access, must disable it for now.
            #send_notifications(version, build)
        else:
            log.warning(LOG_TEMPLATE.format(
                project=version.project.slug, version=version.slug, msg="Failed HTML Build"))


@task
def update_static_metadata(project_pk):
    """Update static metadata JSON file

    Metadata settings include the following project settings:

    version
      The default version for the project, default: `latest`

    language
      The default language for the project, default: `en`

    languages
      List of languages built by linked translation projects.
    """
    project_base = apiv2.project(project_pk)
    project_data = project_base.get()
    project = make_api_project(project_data)
    log.info(LOG_TEMPLATE.format(
        project=project.slug,
        version='',
        msg='Updating static metadata',
    ))
    translations = project_base.translations.get()['translations']
    languages = set([
        translation['language']
        for translation in translations
        if 'language' in translation
    ])
    # Convert to JSON safe types
    metadata = {
        'version': project.default_version,
        'language': project.language,
        'languages': list(languages),
        'single_version': project.single_version,
    }
    try:
        path = project.static_metadata_path()
        fh = open(path, 'w')
        json.dump(metadata, fh)
        fh.close()
        copy_file_to_app_servers(path, path)
    except IOError as e:
        log.debug(LOG_TEMPLATE.format(
            project=project.slug,
            version='',
            msg='Cannot write to metadata.json: {0}'.format(e)
        ))


def create_build(version, api, record):
    """
    Create the build object.
    If we're recording it, save it to the DB.
    Otherwise just use an empty hash.
    """
    if record:
        # Create Build Object.
        build = api.build.post(dict(
            project='/api/v1/project/%s/' % version.project.pk,
            version='/api/v1/version/%s/' % version.pk,
            type='html',
            state='triggered',
            success=True,
        ))
    else:
        build = {}
    return build


def record_build(api, record, build, results, state):
    """
    Record a build by hitting the API.

    Returns nothing
    """

    if not record:
        return None

    setup_steps = ['checkout', 'venv', 'sphinx', 'requirements', 'install']
    output_steps = ['html']
    all_steps = setup_steps + output_steps

    build['state'] = state
    if 'html' in results:
        build['success'] = results['html'][0] == 0
    else:
        build['success'] = False

    # Set global state
    # for step in all_steps:
    #     if results.get(step, False):
    #         if results.get(step)[0] != 0:
    #             results['success'] = False

    build['exit_code'] = max([results.get(step, [0])[0] for step in all_steps])

    build['setup'] = build['setup_error'] = ""
    build['output'] = build['error'] = ""

    for step in setup_steps:
        if step in results:
            build['setup'] += "\n\n%s\n-----\n\n" % step
            build['setup'] += results.get(step)[1]
            build['setup_error'] += "\n\n%s\n-----\n\n" % step
            build['setup_error'] += results.get(step)[2]

    for step in output_steps:
        if step in results:
            build['output'] += "\n\n%s\n-----\n\n" % step
            build['output'] += results.get(step)[1]
            build['error'] += "\n\n%s\n-----\n\n" % step
            build['error'] += results.get(step)[2]
    try:
        ret = api.build(build['id']).put(build)
    except Exception, e:
        log.error("Unable to post a new build", exc_info=True)


def record_pdf(api, record, results, state, version):
    if not record:
        return None
    try:
        api.build.post(dict(
            state=state,
            project='/api/v1/project/%s/' % version.project.pk,
            version='/api/v1/version/%s/' % version.pk,
            success=results['pdf'][0] == 0,
            type='pdf',
            output=results['pdf'][1],
            error=results['pdf'][2],
            exit_code=results['pdf'][0],
        ))
    except Exception, e:
        log.error(LOG_TEMPLATE.format(project=version.project.slug,
                                      version=version.slug, msg="Unable to post a new build"), exc_info=True)


def update_search(version):
    page_list = process_all_json_files(version)
    data = {
        'page_list': page_list,
        'version_pk': version.pk,
        'project_pk': version.project.pk
    }
    log_msg = ' '.join([page['path'] for page in page_list])
    log.info("(Search Index) Sending Data: %s [%s]" % (
        version.project.slug, log_msg))
    apiv2.index_search.post({'data': data})


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
    log.info(LOG_TEMPLATE.format(
        project=project.slug, version=version.slug, msg='Indexing files'))
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
    # End


@task()
def remove_dir(path):
    """
    Remove a directory on the build/celery server.

    This is mainly a wrapper around shutil.rmtree so that app servers
    can kill things on the build server.
    """
    log.info("Removing %s" % path)
    shutil.rmtree(path)

# @task()
# def update_config_from_json(version_pk):
#     """
#     Check out or update the given project's repository.
#     """
# Remove circular import
#     from projects.forms import ImportProjectForm
#     version_data = api.version(version_pk).get()
#     version = make_api_version(version_data)
#     project = version.project
#     log.debug(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Checking for json config"))
#     try:
#         rtd_json = open(os.path.join(
#             project.checkout_path(version.slug),
#             '.rtd.json'
#         ))
#         json_obj = json.load(rtd_json)
#         for key in json_obj.keys():
# Treat the defined fields on the Import form as
# the canonical list of allowed user editable fields.
# This is in essense just another UI for that form.
#             if key not in ImportProjectForm._meta.fields:
#                 del json_obj[key]
#     except IOError:
#         log.debug(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="No rtd.json found."))
#         return None

#     project_data = api.project(project.pk).get()
#     project_data.update(json_obj)
#     api.project(project.pk).put(project_data)
#     log.debug(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg="Updated from JSON."))

# def update_state(version):
#     """
#     Keep state between the repo and the database
#     """
#     log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg='Setting config values from .rtd.yml'))
#     try:
#         update_config_from_json(version.pk)
#     except Exception, e:
# Never kill the build, but log the error
#         log.error(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg='Failure in config parsing code: %s ' % e.message))


# def send_notifications(version, build):
# zenircbot_notification(version.id)
#     for hook in version.project.webhook_notifications.all():
#         webhook_notification.delay(version.project.id, build, hook.url)
#     emails = (version.project.emailhook_notifications.all()
#               .values_list('email', flat=True))
#     for email in emails:
#         email_notification(version.project.id, build, email)


# @task()
# def email_notification(project_id, build, email):
#     if build['success']:
#         return
#     project = Project.objects.get(id=project_id)
#     build_obj = Build.objects.get(id=build['id'])
#     subject = (_('(ReadTheDocs) Building docs for %s failed') % project.name)
#     template = 'projects/notification_email.txt'
#     context = {
#         'project': project.name,
#         'build_url': 'http://%s%s' % (Site.objects.get_current().domain,
#                                       build_obj.get_absolute_url())
#     }
#     message = get_template(template).render(Context(context))

#     send_mail(subject=subject, message=message,
# from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=(email,))


# @task()
# def webhook_notification(project_id, build, hook_url):
#     project = Project.objects.get(id=project_id)
#     data = json.dumps({
#         'name': project.name,
#         'slug': project.slug,
#         'build': {
#             'id': build['id'],
#             'success': build['success'],
#             'date': build['date']
#         }
#     })
#     log.debug(LOG_TEMPLATE.format(project=project.slug, version='', msg='sending notification to: %s' % hook_url))
#     requests.post(hook_url, data=data)

# @task()
# def zenircbot_notification(version_id):
#     version = version.objects.get(id=version_id)
#     message = "build of %s successful" % version
#     redis_obj = redis.redis(**settings.redis)
# irc = getattr(settings, 'irc_channel', '#readthedocs-build')
#     try:
#         redis_obj.publish('out',
#                           json.dumps({
#                               'version': 1,
#                               'type': 'privmsg',
#                               'data': {
#                                   'to': irc,
#                                   'message': message,
#                               }
#                           }))
#     except redis.connectionerror:
#         return

# @task()
# def clear_artifacts(version_pk):
#     """ Remove artifacts from the build server. """
# Stop doing this for now as it causes 403s if people build things back to
# back some times because of a race condition
#     version_data = api.version(version_pk).get()
#     version = make_api_version(version_data)
#     run('rm -rf %s' % version.project.full_epub_path(version.slug))
#     run('rm -rf %s' % version.project.full_man_path(version.slug))
#     run('rm -rf %s' % version.project.full_build_path(version.slug))
#     run('rm -rf %s' % version.project.full_latex_path(version.slug))

# @periodic_task(run_every=crontab(hour="*/12", minute="*", day_of_week="*"))
# def update_mirror_docs():
#     """
#     A periodic task used to update all projects that we mirror.
#     """
#     record = False
#     current = datetime.datetime.now()
# Only record one build a day, at midnight.
#     if current.hour == 0 and current.minute == 0:
#         record = True
#     data = apiv2.project().get(mirror=True, page_size=500)
#     for project_data in data['results']:
#         p = make_api_project(project_data)
#         update_docs(pk=p.pk, record=record)
